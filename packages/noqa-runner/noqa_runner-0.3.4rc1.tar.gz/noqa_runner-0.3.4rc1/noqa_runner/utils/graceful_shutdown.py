"""
Graceful shutdown utilities

Simple utilities for handling graceful application shutdown:
- Signal handling (SIGINT, SIGTERM)
- Task cancellation with timeout

Usage:
    from noqa_runner.utils.graceful_shutdown import (
        install_signal_handlers,
        is_shutdown_requested,
        wait_for_tasks,
    )

    # Install handlers once at startup
    install_signal_handlers()

    # Check in loops
    while not is_shutdown_requested():
        await do_work()

    # Wait for tasks to complete on shutdown
    tasks = [task1, task2, task3]
    await wait_for_tasks(tasks, timeout=60.0)
"""

from __future__ import annotations

import asyncio
import logging
import signal
from typing import Iterable

logger = logging.getLogger(__name__)

# Global shutdown flag
_shutdown_requested = False
_signal_handlers_installed = False

# Simple task registry for backward compatibility
_active_tasks: set[asyncio.Task] = set()


def request_shutdown() -> None:
    """Request graceful shutdown and cancel registered tasks"""
    global _shutdown_requested
    if not _shutdown_requested:
        logger.info("Shutdown requested")
        _shutdown_requested = True

        # Cancel all registered tasks
        for task in _active_tasks.copy():
            if not task.done():
                task.cancel()


def is_shutdown_requested() -> bool:
    """Check if shutdown was requested"""
    return _shutdown_requested


def reset_shutdown_state() -> None:
    """Reset shutdown state (for testing only)"""
    global _shutdown_requested, _signal_handlers_installed
    _shutdown_requested = False
    _signal_handlers_installed = False
    _active_tasks.clear()


def install_signal_handlers() -> None:
    """
    Install signal handlers for graceful shutdown

    Handles SIGINT (Ctrl+C) and SIGTERM (kill) signals.
    Safe to call multiple times - only installs once.
    """
    global _signal_handlers_installed
    if _signal_handlers_installed:
        return

    def _signal_handler(sig: int) -> None:
        logger.info(f"Received signal {sig}, initiating shutdown...")
        request_shutdown()

    try:
        # Try to use event loop's signal handlers (preferred)
        loop = asyncio.get_running_loop()
        if hasattr(signal, "SIGINT"):
            loop.add_signal_handler(
                signal.SIGINT, lambda: _signal_handler(signal.SIGINT)
            )
        if hasattr(signal, "SIGTERM"):
            loop.add_signal_handler(
                signal.SIGTERM, lambda: _signal_handler(signal.SIGTERM)
            )
        _signal_handlers_installed = True
        logger.debug("Signal handlers installed (event loop)")
    except RuntimeError:
        # No event loop running - use standard signal handlers
        if hasattr(signal, "SIGINT"):
            signal.signal(signal.SIGINT, lambda sig, frame: _signal_handler(sig))
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, lambda sig, frame: _signal_handler(sig))
        _signal_handlers_installed = True
        logger.debug("Signal handlers installed (standard)")
    except Exception as e:
        logger.warning(f"Could not install signal handlers: {e}")


async def wait_for_tasks(tasks: Iterable[asyncio.Task], timeout: float = 60.0) -> None:
    """
    Wait for tasks to complete with timeout, cancel remaining on timeout

    Args:
        tasks: Iterable of asyncio tasks to wait for
        timeout: Maximum time to wait in seconds
    """
    task_list = list(tasks)
    if not task_list:
        logger.debug("No tasks to wait for")
        return

    logger.info(f"Waiting for {len(task_list)} tasks (timeout: {timeout}s)")

    try:
        await asyncio.wait_for(
            asyncio.gather(*task_list, return_exceptions=True), timeout=timeout
        )
        logger.info("All tasks completed")
    except asyncio.TimeoutError:
        logger.warning(f"Timeout reached, cancelling {len(task_list)} tasks")
        for task in task_list:
            if not task.done():
                task.cancel()

        # Give tasks brief time to handle cancellation
        try:
            await asyncio.wait_for(
                asyncio.gather(*task_list, return_exceptions=True), timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error("Some tasks did not cancel within 5 seconds")
        except Exception as e:
            logger.error(f"Error during task cancellation: {e}")
    except Exception as e:
        logger.error(f"Error waiting for tasks: {e}")


def register_task(task: asyncio.Task) -> None:
    """
    Register a task for tracking (backward compatibility)

    Note: This is a simple helper. For new code, prefer tracking tasks
    locally and using wait_for_tasks() directly.
    """
    _active_tasks.add(task)
    task.add_done_callback(lambda t: _active_tasks.discard(t))

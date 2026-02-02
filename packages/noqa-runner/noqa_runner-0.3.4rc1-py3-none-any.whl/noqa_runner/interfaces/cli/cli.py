#!/usr/bin/env python3
"""
noqa Runner - CLI for running mobile tests via Agent API

Usage:
    python -m runner run --device-id UDID --appium-url URL --build-path PATH \\
        --noqa-api-token TOKEN --case-input-json JSON
"""

from __future__ import annotations

import asyncio
import json
import uuid

import typer
from typing_extensions import Annotated

from noqa_runner.application.run_test_session import RunnerSession
from noqa_runner.config import sentry_init, settings
from noqa_runner.domain.exceptions import RunnerException
from noqa_runner.domain.models.app_source import AppSource
from noqa_runner.domain.models.platform import Platform
from noqa_runner.domain.models.test_info import RunnerTestInfo
from noqa_runner.logging_config import configure_logging, get_logger
from noqa_runner.utils.graceful_shutdown import install_signal_handlers

app = typer.Typer(
    name="noqa-runner",
    help="noqa Mobile Test Runner - Execute mobile tests via Agent API",
    add_completion=False,
)

logger = get_logger(__name__)


@app.command()
def run(
    noqa_api_token: Annotated[str, typer.Option(help="noqa API authentication token")],
    case_input_json: Annotated[
        str,
        typer.Option(
            help="JSON string with test cases (list of {test_id, case_instructions, bundle_id})"
        ),
    ],
    build_source: Annotated[
        AppSource | None,
        typer.Option(
            help="Application source: file (local build), testflight, or appstore"
        ),
    ] = None,
    build_path: Annotated[
        str | None,
        typer.Option(help="Path to .ipa (device) or .app (simulator) build file"),
    ] = None,
    app_store_id: Annotated[
        str | None,
        typer.Option(
            help="App Store ID for TestFlight or App Store installation (device only)"
        ),
    ] = None,
    app_bundle_id: Annotated[
        str | None,
        typer.Option(
            help="App bundle ID (required for TestFlight/App Store, auto-extracted from build)"
        ),
    ] = None,
    app_context: Annotated[
        str | None, typer.Option(help="Optional application context information")
    ] = None,
    agent_api_url: Annotated[
        str | None, typer.Option(help="Agent API base URL")
    ] = None,
    log_level: Annotated[
        str | None, typer.Option(help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    ] = None,
    appium_url: Annotated[str | None, typer.Option(help="Appium server URL")] = None,
    max_steps: Annotated[
        int | None, typer.Option(help="Maximum number of steps for test execution")
    ] = None,
    appium_capabilities: Annotated[
        str | None, typer.Option(help="Appium capabilities as JSON string")
    ] = None,
    appium_client_config: Annotated[
        str | None, typer.Option(help="Appium client config as JSON string")
    ] = None,
    platform: Annotated[
        Platform, typer.Option(help="Mobile platform (ios or android)")
    ] = Platform.IOS,
):
    """
    Run mobile tests on device or simulator via Agent API

    Example (iOS device with local file build):
        noqa-runner run --noqa-api-token secret --build-source file \\
            --platform ios --build-path /path/to/app.ipa \\
            --case-input-json '[{"test_id":"uuid","case_instructions":"Login"}]'

    Example (iOS simulator with .app build):
        noqa-runner run --noqa-api-token secret --build-source file \\
            --platform ios --build-path /path/to/MyApp.app \\
            --case-input-json '[{"test_id":"uuid","case_instructions":"Login"}]'

    Example (Android device with local APK):
        noqa-runner run --noqa-api-token secret --build-source file \\
            --platform android --build-path /path/to/app.apk \\
            --case-input-json '[{"test_id":"uuid","case_instructions":"Login"}]'

    Example (iOS device with TestFlight):
        noqa-runner run --noqa-api-token secret --build-source testflight \\
            --platform ios \\
            --app-store-id 123456789 \\
            --app-bundle-id com.example.app \\
            --case-input-json '[{"test_id":"uuid","case_instructions":"Login"}]'

    Example (iOS device with App Store):
        noqa-runner run --noqa-api-token secret --build-source appstore \\
            --platform ios \\
            --app-store-id 123456789 \\
            --app-bundle-id com.example.app \\
            --case-input-json '[{"test_id":"uuid","case_instructions":"Login"}]'
    """
    # Validate source parameter combinations
    if build_source == AppSource.FILE and not build_path:
        typer.echo(
            "Error: --build-path is required when --build-source is 'file'", err=True
        )
        raise typer.Exit(code=1)

    if build_source in (AppSource.TESTFLIGHT, AppSource.APPSTORE) and not app_store_id:
        typer.echo(
            f"Error: --app-store-id is required when --build-source is '{build_source.value}'",
            err=True,
        )
        raise typer.Exit(code=1)

    if build_source in (AppSource.TESTFLIGHT, AppSource.APPSTORE) and not app_bundle_id:
        typer.echo(
            f"Error: --app-bundle-id is required when --build-source is '{build_source.value}'",
            err=True,
        )
        raise typer.Exit(code=1)

    # Validate platform and build_path correspondence
    if build_source == AppSource.FILE and build_path:
        if platform == Platform.ANDROID:
            if not build_path.lower().endswith(".apk"):
                raise typer.BadParameter(
                    f"For Android (--platform android), build file must have .apk extension. "
                    f"Got: {build_path}. "
                    f"Example: --platform android --build-path /path/to/app.apk"
                )
        elif platform == Platform.IOS:
            if not (
                build_path.lower().endswith(".ipa")
                or build_path.lower().endswith(".app")
            ):
                raise typer.BadParameter(
                    f"For iOS (--platform ios), build file must have .ipa or .app extension. "
                    f"Got: {build_path}. "
                    f"Examples: --platform ios --build-path /path/to/app.ipa "
                    f"or --platform ios --build-path /path/to/MyApp.app"
                )

    try:
        asyncio.run(
            _run_async(
                app_build_path=build_path,
                app_store_id=app_store_id,
                app_bundle_id=app_bundle_id,
                noqa_api_token=noqa_api_token,
                case_input_json=case_input_json,
                app_context=app_context,
                agent_api_url=agent_api_url,
                log_level=log_level,
                appium_url=appium_url,
                max_steps=max_steps,
                appium_capabilities=appium_capabilities,
                appium_client_config=appium_client_config,
                build_source=build_source,
                platform=platform,
            )
        )
    except (KeyboardInterrupt, SystemExit):
        # Graceful shutdown on external termination
        typer.echo("\n⚠️  Test interrupted by user", err=True)
        raise typer.Exit(code=130)  # Standard exit code for SIGINT


async def _run_async(
    noqa_api_token: str,
    case_input_json: str,
    app_build_path: str | None,
    app_store_id: str | None,
    app_bundle_id: str | None,
    app_context: str | None,
    agent_api_url: str | None,
    log_level: str | None,
    appium_url: str | None,
    max_steps: int | None,
    appium_capabilities: str | None,
    appium_client_config: str | None,
    build_source: AppSource | None,
    platform: Platform,
):
    # Apply defaults
    if log_level is None:
        log_level = "INFO"

    # Configure logging
    configure_logging(is_simple=True, log_level=log_level)

    # Initialize Sentry
    sentry_init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT)

    # Install signal handlers for graceful shutdown
    install_signal_handlers()

    if not case_input_json:
        logger.error(
            "validation_error",
            error="Either --case-input-json or --case-ids must be provided",
        )
        typer.echo(
            "Error: Either --case-input-json or --case-ids must be provided", err=True
        )
        raise typer.Exit(code=1)

    # Parse test cases from JSON
    try:
        tests_data = json.loads(case_input_json)
        tests = [
            RunnerTestInfo(
                test_id=test.get("test_id", uuid.uuid4().hex),
                case_instructions=test["case_instructions"],
                case_name=test.get("case_name", ""),
            )
            for test in tests_data
        ]
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error("json_parse_error", error=str(e))
        typer.echo(f"Error: Invalid JSON format: {e}", err=True)
        raise typer.Exit(code=1)

    # Run tests using application
    test_session = RunnerSession()
    try:
        # Parse Appium parameters from JSON strings
        appium_caps: dict | None = None
        appium_config: dict | None = None

        if appium_capabilities:
            appium_caps = json.loads(appium_capabilities)

        if appium_client_config:
            appium_config = json.loads(appium_client_config)

        results = await test_session.execute(
            noqa_api_token=noqa_api_token,
            tests=tests,
            app_context=app_context,
            app_bundle_id=app_bundle_id,
            app_store_id=app_store_id,
            app_build_path=app_build_path,
            appium_url=appium_url,
            agent_api_url=agent_api_url,
            max_steps=max_steps,
            appium_capabilities=appium_caps,
            appium_client_config=appium_config,
            build_source=build_source,
            platform=platform,
        )

        # Output results as JSON
        results_json = json.dumps(
            [result.export_dict() for result in results], indent=2
        )
        typer.echo(results_json)
    except RunnerException as e:
        # All runner exceptions (BuildNotFoundError, AppiumConnectionError, etc.)
        logger.error("runner_error", error=str(e), error_type=type(e).__name__)
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)
    except asyncio.CancelledError:
        # Tests were cancelled - this is expected on shutdown
        logger.info("Test session cancelled by shutdown signal")
        typer.echo("\n⚠️  Tests interrupted by shutdown signal", err=True)
        raise typer.Exit(code=130)


@app.command()
def run_cloud():
    """Run tests on AWS Device Farm (not implemented yet)"""
    typer.echo("⚠️  run_cloud command is not implemented yet")
    typer.echo("This command will allow running tests on AWS Device Farm in the future")
    raise typer.Exit(code=1)


def main():
    """Entry point for CLI"""
    # Typer doesn't automatically handle async functions, so we need to wrap the app call
    app()


if __name__ == "__main__":
    main()

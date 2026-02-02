from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from zipfile import ZipFile

import aiofiles

from noqa_runner.utils.retry_decorator import with_retry


class LocalStorageAdapter:
    """Generic adapter for managing file storage (local filesystem)"""

    def __init__(self, output_dir: str | None = None):
        if output_dir:
            base_dir = Path(output_dir)
            base_dir.mkdir(parents=True, exist_ok=True)
            self.base_dir = base_dir
        else:
            # Fallback to temporary directory
            self.base_dir = Path(tempfile.mkdtemp(prefix="agent_temp_"))

    @with_retry(
        max_attempts=3,
        exceptions=(OSError, IOError),
        exclude_exceptions=(FileNotFoundError,),
    )
    async def read_file(self, path: str) -> bytes:
        """Read file from local filesystem (supports absolute and relative paths)"""
        file_path = Path(path)

        # Handle absolute and relative paths
        is_absolute = file_path.is_absolute()
        if is_absolute:
            file_path = file_path.resolve()
        else:
            file_path = (self.base_dir / file_path).resolve()
            # Validate relative path is within base_dir (prevent path traversal)
            try:
                file_path.relative_to(self.base_dir.resolve())
            except ValueError:
                raise ValueError(f"Path traversal detected: {path}")

        try:
            async with aiofiles.open(file_path, "rb") as f:
                return await f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")

    @with_retry(max_attempts=3, exceptions=(OSError, IOError))
    async def save_file(self, path: str, data: bytes) -> None:
        """Save file to local filesystem (supports absolute and relative paths)"""
        file_path = Path(path)

        # Handle absolute and relative paths
        is_absolute = file_path.is_absolute()
        if is_absolute:
            file_path = file_path.resolve()
        else:
            file_path = (self.base_dir / file_path).resolve()
            # Validate relative path is within base_dir (prevent path traversal)
            try:
                file_path.relative_to(self.base_dir.resolve())
            except ValueError:
                raise ValueError(f"Path traversal detected: {path}")

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(data)

    @with_retry(
        max_attempts=3,
        exceptions=(OSError, IOError),
        exclude_exceptions=(FileNotFoundError,),
    )
    async def extract_file_from_zip(self, zip_path: str, filename: str) -> bytes | None:
        """
        Extract specific file from local ZIP archive

        Args:
            zip_path: Path to the local ZIP file (relative to base_dir, or absolute if within base_dir)
            filename: Name of the file to extract (can be partial path, e.g., ".app/Info.plist")

        Returns:
            File content as bytes, or None if file not found
        """
        file_path = Path(zip_path)

        # Resolve relative to base_dir
        file_path = (self.base_dir / file_path).resolve()

        # Validate path is within base_dir (prevent path traversal)
        try:
            file_path.relative_to(self.base_dir.resolve())
        except ValueError:
            raise ValueError(f"Path traversal detected: {zip_path}")

        # Offload blocking ZIP operations to thread pool
        return await asyncio.to_thread(
            self._extract_file_from_zip_sync, file_path, filename
        )

    def _extract_file_from_zip_sync(
        self, file_path: Path, filename: str
    ) -> bytes | None:
        """Synchronous helper for ZIP file extraction"""
        with ZipFile(file_path, "r") as zip_file:
            matches = [path for path in zip_file.namelist() if path.endswith(filename)]
            if len(matches) > 1:
                raise ValueError(
                    f"Multiple files found matching '{filename}': {matches}"
                )
            if matches:
                return zip_file.read(matches[0])

        return None

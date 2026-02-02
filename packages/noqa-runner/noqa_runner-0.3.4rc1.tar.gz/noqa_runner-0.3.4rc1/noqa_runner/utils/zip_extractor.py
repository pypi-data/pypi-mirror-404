"""Utility for extracting files from local ZIP archives"""

from __future__ import annotations

from zipfile import ZipFile


def extract_file_from_zip(zip_path: str, filename: str) -> bytes | None:
    """
    Extract specific file from local ZIP archive

    Args:
        zip_path: Path to the local ZIP file
        filename: Name of the file to extract (can be partial path, e.g., ".app/Info.plist")

    Returns:
        File content as bytes, or None if file not found
    """
    with ZipFile(zip_path, "r") as zip_file:
        matches = [path for path in zip_file.namelist() if path.endswith(filename)]
        if len(matches) > 1:
            raise ValueError(f"Multiple files match '{filename}': {matches}")
        if matches:
            return zip_file.read(matches[0])

    return None

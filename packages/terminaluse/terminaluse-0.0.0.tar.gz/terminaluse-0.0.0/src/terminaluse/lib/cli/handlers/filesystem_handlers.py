"""
Filesystem CLI handlers for creating and managing filesystems.

This module provides core filesystem-related logic for the CLI.
"""

from __future__ import annotations

import uuid
import shutil
import asyncio
from pathlib import Path

from terminaluse import TerminalUse
from terminaluse.lib.utils.logging import make_logger
from terminaluse.types.filesystem_response import FilesystemResponse
from terminaluse.lib.utils.filesystem_archive import (
    FilesystemNotFoundError,
    create_archive,
    extract_archive,
    upload_to_presigned_url,
    download_from_presigned_url,
)
from terminaluse.lib.utils.filesystem_manifest import FilesystemManifest

logger = make_logger(__name__)


class FilesystemError(Exception):
    """Base exception for filesystem operations."""

    pass


def create_filesystem(
    client: TerminalUse,
    project_id: str,
    name: str | None = None,
) -> FilesystemResponse:
    """
    Create a new filesystem.

    Args:
        client: The TerminalUse client instance
        project_id: Project ID this filesystem belongs to
        name: Optional human-readable name for the filesystem

    Returns:
        Created FilesystemResponse object

    Raises:
        Exception: If filesystem creation fails
    """
    return client.filesystems.create(
        project_id=project_id,
        name=name,
    )


def push_directory(
    client: TerminalUse,
    filesystem_id: str,
    local_path: Path,
) -> tuple[int, int, int]:
    """
    Upload local directory to filesystem.

    Args:
        client: The TerminalUse client instance
        filesystem_id: Filesystem ID to upload to
        local_path: Local directory path to upload

    Returns:
        Tuple of (files_count, uncompressed_size_bytes, compressed_size_bytes)

    Raises:
        FilesystemError: If directory doesn't exist or upload fails
    """
    if not local_path.exists():
        raise FilesystemError(f"Directory not found: {local_path}")

    if not local_path.is_dir():
        raise FilesystemError(f"Path is not a directory: {local_path}")

    # Build manifest with content extraction for text files
    manifest_builder = FilesystemManifest(local_path, skip_patterns=[])
    manifest_result = asyncio.run(manifest_builder.check_dirty_and_build())

    # Create archive for upload (skip patterns match manifest)
    archive_result = asyncio.run(
        create_archive(
            local_path=local_path,
            skip_patterns=[],
        )
    )

    # Get presigned upload URL
    upload_url_response = client.filesystems.get_upload_url(filesystem_id)
    upload_url = upload_url_response.url

    # Upload archive via presigned URL
    asyncio.run(
        upload_to_presigned_url(
            url=upload_url,
            data=archive_result.data,
        )
    )

    # Generate sync_id for idempotency
    sync_id = str(uuid.uuid4())

    # Convert manifest entries to dict format for API
    files_payload = [
        {
            "path": entry.path,
            "is_directory": entry.is_directory,
            "size_bytes": entry.size_bytes,
            "checksum": entry.checksum,
            "mime_type": entry.mime_type,
            "modified_at": entry.modified_at.isoformat(),
            "content": entry.content,
            "is_binary": entry.is_binary,
            "content_truncated": entry.content_truncated,
        }
        for entry in manifest_result.entries
    ]

    # Call sync_complete with manifest including content
    client.filesystems.sync_complete(
        filesystem_id=filesystem_id,
        direction="UP",
        status="SUCCESS",
        sync_id=sync_id,
        archive_checksum=archive_result.checksum,
        archive_size_bytes=archive_result.size_bytes,
        files=files_payload,
    )

    return (
        archive_result.files_count,
        archive_result.uncompressed_size_bytes,
        archive_result.size_bytes,
    )


def pull_directory(
    client: TerminalUse,
    filesystem_id: str,
    local_path: Path,
    force: bool = False,
) -> tuple[int, int]:
    """
    Download filesystem to local directory.

    Args:
        client: The TerminalUse client instance
        filesystem_id: Filesystem ID to download from
        local_path: Local directory path to download to
        force: If True, clear existing directory contents before extracting

    Returns:
        Tuple of (files_count, bytes_extracted)

    Raises:
        FilesystemError: If directory exists with files and force=False
        FilesystemNotFoundError: If filesystem archive doesn't exist
    """
    # Check if local path exists and has files
    if local_path.exists():
        if local_path.is_file():
            raise FilesystemError(f"Path exists and is a file: {local_path}")

        # Check if directory has any files
        has_files = any(local_path.iterdir())
        if has_files:
            if not force:
                raise FilesystemError(
                    f"Directory {local_path} already exists and contains files.\n"
                    "Use --force to overwrite."
                )
            # Clear directory contents before extraction to avoid orphan files
            for item in local_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
    else:
        # Create directory if it doesn't exist
        local_path.mkdir(parents=True, exist_ok=True)

    # Get presigned download URL
    download_url_response = client.filesystems.get_download_url(filesystem_id)
    download_url = download_url_response.url

    # Download archive via presigned URL
    try:
        archive_data = asyncio.run(download_from_presigned_url(url=download_url))
    except FilesystemNotFoundError as err:
        raise FilesystemError(
            f"Filesystem {filesystem_id} has no archive. "
            "This may be a new filesystem that hasn't been pushed to yet."
        ) from err

    # Extract to local path
    extract_result = asyncio.run(
        extract_archive(
            archive_data=archive_data,
            local_path=local_path,
        )
    )

    return extract_result.files_count, extract_result.bytes_extracted


def list_filesystems(
    client: TerminalUse,
    project_id: str,
) -> list[FilesystemResponse]:
    """
    List all filesystems for a project.

    Args:
        client: The TerminalUse client instance
        project_id: Project ID to filter by

    Returns:
        List of FilesystemResponse objects for the project
    """
    # Get all filesystems accessible to the user
    # FilesystemListResponse is a type alias for List[FilesystemResponse]
    all_filesystems = client.filesystems.list()

    # Filter by project_id
    return [fs for fs in all_filesystems if fs.project_id == project_id]


def list_all_filesystems(
    client: TerminalUse,
) -> tuple[list[FilesystemResponse], dict[str, str]]:
    """
    List all filesystems across all projects.

    Args:
        client: The TerminalUse client instance

    Returns:
        Tuple of (filesystems list, project_id -> project_name map)
    """
    # Get all filesystems accessible to the user
    all_filesystems = list(client.filesystems.list())

    # Get all projects to build a name lookup map
    all_projects = list(client.projects.list())
    project_map = {p.id: p.name for p in all_projects}

    return all_filesystems, project_map


def get_filesystem(client: TerminalUse, filesystem_id: str) -> FilesystemResponse:
    """
    Get filesystem details by ID.

    Args:
        client: The TerminalUse client instance
        filesystem_id: Filesystem ID to retrieve

    Returns:
        FilesystemResponse object
    """
    return client.filesystems.retrieve(filesystem_id)


def get_filesystem_file_count(client: TerminalUse, filesystem_id: str) -> int:
    """
    Get the number of files in a filesystem.

    Args:
        client: The TerminalUse client instance
        filesystem_id: Filesystem ID to query

    Returns:
        Number of files in the filesystem
    """
    try:
        response = client.filesystems.list_files(filesystem_id)
        # Response has total_count attribute
        return response.total_count
    except Exception:
        # If listing files fails (e.g., empty filesystem), return 0
        return 0


def format_filesystem_summary(fs: FilesystemResponse, file_count: int | None = None) -> str:
    """
    Format filesystem details as human-readable summary.

    Args:
        fs: FilesystemResponse object
        file_count: Optional file count to include in size display

    Returns:
        Formatted string summary
    """
    lines = []
    lines.append(f"Filesystem: {fs.id}")
    lines.append(f"Name:       {fs.name or '(unnamed)'}")
    lines.append(f"Status:     {fs.status}")

    # Format size with optional file count
    if fs.archive_size_bytes is not None:
        size_str = _format_bytes(fs.archive_size_bytes)
        if file_count is not None and file_count > 0:
            size_str = f"{size_str} ({file_count} files)"
    else:
        size_str = "0 B"
    lines.append(f"Size:       {size_str}")

    # Format created timestamp
    if fs.created_at:
        created_str = fs.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        created_str = "unknown"
    lines.append(f"Created:    {created_str}")

    # Format last sync timestamp
    if fs.last_synced_at:
        synced_str = fs.last_synced_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        synced_str = "never"
    lines.append(f"Last Sync:  {synced_str}")

    return "\n".join(lines)


def format_filesystems_table(
    filesystems: list[FilesystemResponse],
    project_id: str,
) -> str:
    """
    Format list of filesystems as a table.

    Args:
        filesystems: List of FilesystemResponse objects
        project_id: Project ID being listed

    Returns:
        Formatted table string
    """
    if not filesystems:
        return f"No filesystems found for project {project_id}"

    lines = []
    lines.append(f"Filesystems for project {project_id}:\n")

    # Header
    lines.append(f"  {'ID':<36}  {'Name':<18}  {'Size':<10}  {'Last Sync':<16}")

    for fs in filesystems:
        fs_id = fs.id
        name = (fs.name or "(unnamed)")[:18]

        if fs.archive_size_bytes is not None:
            size = _format_bytes(fs.archive_size_bytes)[:10]
        else:
            size = "0 B"

        if fs.last_synced_at:
            synced = fs.last_synced_at.strftime("%Y-%m-%d %H:%M")
        else:
            synced = "never"

        lines.append(f"  {fs_id:<36}  {name:<18}  {size:<10}  {synced:<16}")

    lines.append(f"\nTotal: {len(filesystems)} filesystem(s)")
    return "\n".join(lines)


def format_filesystems_table_all_projects(
    filesystems: list[FilesystemResponse],
    project_map: dict[str, str],
) -> str:
    """
    Format list of filesystems from all projects as a table.

    Args:
        filesystems: List of FilesystemResponse objects
        project_map: Mapping of project_id -> project_name

    Returns:
        Formatted table string
    """
    if not filesystems:
        return "No filesystems found"

    lines = []
    lines.append("Filesystems:\n")

    # Header with Project column
    lines.append(f"  {'ID':<36}  {'Name':<14}  {'Project':<16}  {'Size':<10}  {'Last Sync':<16}")

    for fs in filesystems:
        fs_id = fs.id
        name = (fs.name or "(unnamed)")[:14]
        proj_id = fs.project_id or "(unknown)"
        project_name = project_map.get(proj_id, proj_id)[:16]

        if fs.archive_size_bytes is not None:
            size = _format_bytes(fs.archive_size_bytes)[:10]
        else:
            size = "0 B"

        if fs.last_synced_at:
            synced = fs.last_synced_at.strftime("%Y-%m-%d %H:%M")
        else:
            synced = "never"

        lines.append(f"  {fs_id:<36}  {name:<14}  {project_name:<16}  {size:<10}  {synced:<16}")

    lines.append(f"\nTotal: {len(filesystems)} filesystem(s)")
    return "\n".join(lines)


def _format_bytes(size_bytes: int) -> str:
    """Format bytes as human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

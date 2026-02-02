"""
Filesystem sync module for the Agent Development Kit (ADK).

This module provides high-level async methods for filesystem sync operations:
- sync_down: Download filesystem from GCS if changed
- sync_up: Upload filesystem to GCS if changed

Optimizations:
- Skip download if archive checksum unchanged
- Skip upload if no files modified (mtime check)
- Background manifest building for sync_down
"""

from __future__ import annotations

import uuid
import asyncio
from pathlib import Path
from dataclasses import dataclass

import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from typing import Any

from terminaluse import AsyncTerminalUse
# FilesystemFileParam was a Stainless TypedDict; use dict instead
from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.environment_variables import EnvironmentVariables
from terminaluse.lib.utils.file_utils import atomic_json_write
from terminaluse.lib.utils.filesystem_archive import (
    ArchiveResult,
    FilesystemSyncError,
    CorruptArchiveError,
    FilesystemNotFoundError,
    create_archive,
    extract_archive,
    upload_to_presigned_url,
    download_from_presigned_url,
)
from terminaluse.lib.utils.filesystem_manifest import (
    DEFAULT_SKIP_PATTERNS,
    SyncCache,
    ManifestEntry,
    FilesystemManifest,
    ManifestTooLargeError,
    validate_manifest_size,
)
from terminaluse.lib.adk.utils._modules.client import create_async_terminaluse_client

logger = make_logger(__name__)

# HTTP retry configuration constants for sync-complete API calls
SYNC_COMPLETE_RETRY_STOP = stop_after_attempt(2)  # Initial attempt + 1 retry
SYNC_COMPLETE_RETRY_WAIT = wait_exponential(multiplier=1, min=1, max=10)
SYNC_COMPLETE_RETRY_CONDITION = retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))

# Re-export exceptions for convenience
__all__ = [
    "FilesystemModule",
    "SyncDownResult",
    "SyncUpResult",
    "FilesystemSyncError",
    "CorruptArchiveError",
    "FilesystemNotFoundError",
    "ManifestTooLargeError",
]


@dataclass
class SyncDownResult:
    """Result of sync_down operation."""

    skipped: bool
    reason: str | None = None
    files_extracted: int | None = None
    manifest_pending: bool = False  # True if background task running


@dataclass
class SyncUpResult:
    """Result of sync_up operation."""

    skipped: bool
    reason: str | None = None
    files_uploaded: int | None = None
    archive_size_bytes: int | None = None


class FilesystemModule:
    """
    Module for filesystem sync operations in TerminalUse.

    Provides high-level async methods for:
    - sync_down: Download filesystem from GCS if changed
    - sync_up: Upload filesystem to GCS if changed

    Optimizations:
    - Skip download if archive checksum unchanged
    - Skip upload if no files modified (mtime check)
    - Background manifest building for sync_down
    """

    def __init__(
        self,
        client: AsyncTerminalUse | None = None,
        local_filesystem_path: Path | None = None,
    ):
        """
        Initialize filesystem module.

        Args:
            client: Optional TerminalUse client (creates new if not provided)
            local_filesystem_path: Override default filesystem path
        """
        self._client = client
        self._local_filesystem_path = local_filesystem_path
        self._background_tasks: list[asyncio.Task[None]] = []
        self._skip_patterns = list(DEFAULT_SKIP_PATTERNS)

    def _get_client(self) -> AsyncTerminalUse:
        """Get or create the TerminalUse client lazily."""
        if self._client is None:
            self._client = create_async_terminaluse_client()
        return self._client

    def _get_filesystem_path(self, filesystem_id: str) -> Path:
        """
        Get local path for filesystem.

        Priority:
        1. self._local_filesystem_path (if set)
        2. DATA_ROOT_PATH environment variable + /filesystems/{id}
        3. Default: /bucket_data/filesystems/{filesystem_id}
        """
        if self._local_filesystem_path:
            return self._local_filesystem_path

        # Check for TERMINALUSE_DATA_ROOT_PATH environment variable
        env_vars = EnvironmentVariables.refresh()
        if env_vars.TERMINALUSE_DATA_ROOT_PATH:
            return Path(env_vars.TERMINALUSE_DATA_ROOT_PATH) / "filesystems" / filesystem_id

        # Default filesystem path
        return Path(f"/bucket_data/filesystems/{filesystem_id}")

    async def sync_down(
        self,
        filesystem_id: str,
        local_path: Path | None = None,
    ) -> SyncDownResult:
        """
        Download filesystem from GCS if changed.

        Flow:
        1. Load local sync cache, get archive_checksum
        2. GET /filesystems/{id} -> get remote archive_checksum
        3. If no remote checksum -> return empty_filesystem (no archive yet)
        4. If checksums match -> return skipped=True (~50ms)
        5. POST /filesystems/{id}/download-url -> get presigned URL
        6. Download archive via presigned URL
        7. Extract to local_path
        8. Return immediately (agent can start)
        9. (Background) Build manifest + POST /sync-complete

        Background task allows agent to start immediately after extraction,
        saving 200-600ms of blocking time.

        Args:
            filesystem_id: ID of the filesystem to sync
            local_path: Optional override for local filesystem path

        Returns:
            SyncDownResult with sync status
        """
        local_path = local_path or self._get_filesystem_path(filesystem_id)
        try:
            local_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise FilesystemSyncError(f"Failed to create filesystem directory {local_path}: {e}") from e

        client = self._get_client()

        # 1. Load local cache
        sync_cache = SyncCache(local_path)
        local_checksum = sync_cache.get_archive_checksum()

        # 2. Get remote filesystem state
        filesystem = await client.filesystems.retrieve(filesystem_id)
        remote_checksum: str | None = filesystem.archive_checksum

        # 3. Fast path: no archive exists yet (new/empty filesystem)
        if remote_checksum is None:
            logger.debug(f"Filesystem {filesystem_id} has no archive yet - treating as empty")
            return SyncDownResult(
                skipped=False,
                reason="empty_filesystem",
                files_extracted=0,
                manifest_pending=False,
            )

        # 4. Fast path: unchanged
        if local_checksum == remote_checksum:
            logger.debug(f"Filesystem {filesystem_id} unchanged, skipping download")
            return SyncDownResult(skipped=True, reason="unchanged")

        # 5. Get presigned URL
        url_response = await client.filesystems.get_download_url(filesystem_id)

        # 6. Download archive - handle 404/403 as empty filesystem (fallback)
        try:
            logger.info(f"Downloading filesystem {filesystem_id}")
            archive_data = await download_from_presigned_url(url_response.url)
        except FilesystemNotFoundError:
            logger.info(f"Filesystem {filesystem_id} archive not found - treating as empty")
            return SyncDownResult(
                skipped=False,
                reason="empty_filesystem",
                files_extracted=0,
                manifest_pending=False,
            )

        # 7. Extract to filesystem
        try:
            result = await extract_archive(archive_data, local_path)
            logger.info(f"Extracted {result.files_count} files to {local_path}")
        except CorruptArchiveError as e:
            logger.error(f"Corrupt archive for filesystem {filesystem_id}: {e}")
            raise

        # 8. Schedule background sync-complete (NON-BLOCKING)
        sync_id = str(uuid.uuid4())
        task = asyncio.create_task(
            self._background_sync_complete(
                filesystem_id=filesystem_id,
                local_path=local_path,
                sync_id=sync_id,
                direction="DOWN",
                archive_checksum=remote_checksum,
                archive_size_bytes=len(archive_data),
            )
        )
        self._background_tasks.append(task)

        # Return immediately - agent can start now
        return SyncDownResult(
            skipped=False,
            files_extracted=result.files_count,
            manifest_pending=True,
        )

    async def sync_up(
        self,
        filesystem_id: str,
        local_path: Path | None = None,
    ) -> SyncUpResult:
        """
        Upload filesystem to GCS if changed.

        Flow:
        1. Build manifest with dirty detection
           - Stat scan all files, compare mtime to cache
           - If no changes -> return skipped=True (~10ms)
        2. For changed files: read, hash, build full manifest
        3. Create tar.zst archive
        4. POST /filesystems/{id}/upload-url -> get presigned URL
        5. Upload archive via presigned URL
        6. POST /filesystems/{id}/sync-complete with manifest
        7. Update local caches
        8. Return result

        WARNING: sync_up CANNOT be async/background because:
        - Agent completed -> results need to be persisted
        - If pod dies before upload -> DATA LOSS
        - Caller needs confirmation that sync succeeded

        Args:
            filesystem_id: ID of the filesystem to sync
            local_path: Optional override for local filesystem path

        Returns:
            SyncUpResult with sync status
        """
        local_path = local_path or self._get_filesystem_path(filesystem_id)

        if not local_path.exists():
            logger.warning(f"Filesystem path {local_path} does not exist")
            return SyncUpResult(skipped=True, reason="no_filesystem")

        client = self._get_client()

        # 1. Check for changes using manifest builder
        manifest_builder = FilesystemManifest(local_path, self._skip_patterns)
        manifest_result = await manifest_builder.check_dirty_and_build()

        # Fast path: nothing changed
        if not manifest_result.is_dirty and manifest_result.from_cache:
            logger.debug(f"Filesystem {filesystem_id} unchanged, skipping upload")
            return SyncUpResult(skipped=True, reason="unchanged")

        # Validate manifest size before proceeding
        try:
            validate_manifest_size(manifest_result.entries)
        except ManifestTooLargeError as e:
            logger.error(f"Filesystem {filesystem_id} manifest too large: {e}")
            raise

        # 2. Create archive
        logger.info(f"Creating archive for filesystem {filesystem_id}")
        archive_result: ArchiveResult = await create_archive(local_path, self._skip_patterns)

        # 3. Get presigned URL
        url_response = await client.filesystems.get_upload_url(filesystem_id)

        # 4. Upload archive
        logger.info(f"Uploading {archive_result.size_bytes} bytes to GCS")
        await upload_to_presigned_url(url_response.url, archive_result.data)

        # 5. Complete sync
        sync_id = str(uuid.uuid4())
        files_payload = self._build_files_payload(manifest_result.entries)

        await self._call_sync_complete(
            filesystem_id=filesystem_id,
            sync_id=sync_id,
            direction="UP",
            status="SUCCESS",
            archive_size_bytes=archive_result.size_bytes,
            archive_checksum=archive_result.checksum,
            files=files_payload,
        )

        # 6. Update local cache (using atomic write)
        sync_cache = SyncCache(local_path)
        sync_cache.set_archive_checksum(archive_result.checksum)

        return SyncUpResult(
            skipped=False,
            files_uploaded=len(manifest_result.entries),
            archive_size_bytes=archive_result.size_bytes,
        )

    def _build_files_payload(self, entries: list[ManifestEntry]) -> list[dict[str, Any]]:
        """Convert ManifestEntry list to API payload format."""
        return [
            {
                "path": e.path,
                "is_directory": e.is_directory,
                "size_bytes": e.size_bytes,
                "checksum": e.checksum,
                "mime_type": e.mime_type,
                "modified_at": e.modified_at.isoformat(),
                "content": e.content,
                "is_binary": e.is_binary,
                "content_truncated": e.content_truncated,
            }
            for e in entries
        ]

    async def _background_sync_complete(
        self,
        filesystem_id: str,
        local_path: Path,
        sync_id: str,
        direction: str,
        archive_checksum: str | None,
        archive_size_bytes: int,
    ) -> None:
        """
        Background task to build manifest and notify nucleus.

        Errors are logged but don't fail - agent is already running.
        """
        try:
            # Build manifest
            manifest_builder = FilesystemManifest(local_path, self._skip_patterns)
            manifest_result = await manifest_builder.check_dirty_and_build()

            # Validate manifest size before sending
            try:
                validate_manifest_size(manifest_result.entries)
            except ManifestTooLargeError as e:
                logger.warning(f"Filesystem {filesystem_id} manifest too large, skipping sync-complete: {e}")
                return

            files_payload = self._build_files_payload(manifest_result.entries)

            # Notify nucleus
            await self._call_sync_complete(
                filesystem_id=filesystem_id,
                sync_id=sync_id,
                direction=direction,
                status="SUCCESS",
                archive_size_bytes=archive_size_bytes,
                archive_checksum=archive_checksum,
                files=files_payload,
            )

            # Update local cache
            sync_cache = SyncCache(local_path)
            if archive_checksum:
                sync_cache.set_archive_checksum(archive_checksum)

            logger.debug(f"Background sync-complete finished for {filesystem_id}")

        except httpx.TimeoutException:
            logger.warning(
                f"Background sync-complete timed out for {filesystem_id} (manifest not stored, will retry on next sync)"
            )
        except httpx.HTTPStatusError as e:
            logger.warning(
                f"Background sync-complete HTTP error for {filesystem_id}: "
                f"{e.response.status_code} - {e.response.text[:200]}"
            )
        except Exception as e:
            # Log unexpected errors at ERROR level for visibility
            logger.error(
                f"Background sync-complete failed unexpectedly for {filesystem_id}: {e}",
                exc_info=True,
            )

    @retry(stop=SYNC_COMPLETE_RETRY_STOP, wait=SYNC_COMPLETE_RETRY_WAIT, retry=SYNC_COMPLETE_RETRY_CONDITION)
    async def _call_sync_complete(
        self,
        filesystem_id: str,
        sync_id: str,
        direction: str,
        status: str,
        archive_size_bytes: int | None,
        archive_checksum: str | None,
        files: list[dict[str, Any]],
    ) -> None:
        """
        Call POST /filesystems/{id}/sync-complete via generated SDK with retry.

        Retries once on transient network failures (TimeoutException, ConnectError).
        """
        client = self._get_client()

        await client.filesystems.sync_complete(
            filesystem_id,
            sync_id=sync_id,
            direction=direction,
            status=status,
            archive_size_bytes=archive_size_bytes,
            archive_checksum=archive_checksum,
            files=files,
        )

    async def wait_for_background_tasks(self, timeout: float = 30.0) -> None:
        """
        Wait for background sync-complete tasks to finish.

        Call on graceful shutdown to ensure all manifests are stored.

        Args:
            timeout: Maximum time to wait for background tasks
        """
        if not self._background_tasks:
            return

        _, pending = await asyncio.wait(
            self._background_tasks,
            timeout=timeout,
        )

        for task in pending:
            logger.warning("Cancelling pending background sync task")
            task.cancel()

        self._background_tasks.clear()


# Singleton instance for ADK usage
filesystem = FilesystemModule()

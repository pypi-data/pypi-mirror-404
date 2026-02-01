"""
Task system folder sync module for the Agent Development Kit (ADK).

This module provides high-level async methods for task system folder (.claude) sync operations:
- sync_down_system_folder: Download .claude folder from GCS if changed
- sync_up_system_folder: Upload .claude folder to GCS if changed

The system folder is task-scoped (unique per task) and synced to/from GCS at runtime.
"""

from __future__ import annotations

import os
import json
import uuid
from pathlib import Path
from typing import Literal

import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from terminaluse import AsyncTerminalUse
from terminaluse.lib.utils.logging import make_logger
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
from terminaluse.lib.types.system_folders import SyncDownResult, SyncUpResult
from terminaluse.lib.adk.utils._modules.client import create_async_terminaluse_client

logger = make_logger(__name__)

# Data root from environment, defaults to /bucket_data
DATA_ROOT_PATH = os.environ.get("TERMINALUSE_DATA_ROOT_PATH", "/bucket_data")

# The only system folder type we support
DOT_CLAUDE_CONFIG = {
    "type": "dot_claude",
    "host_path": ".claude",
    "sandbox_mount_path": "/root/.claude",
}

# HTTP retry configuration constants for sync-complete API calls
SYNC_COMPLETE_RETRY_STOP = stop_after_attempt(2)  # Initial attempt + 1 retry
SYNC_COMPLETE_RETRY_WAIT = wait_exponential(multiplier=1, min=1, max=10)
SYNC_COMPLETE_RETRY_CONDITION = retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))

# Skip patterns for .claude folder
SYSTEM_FOLDER_SKIP_PATTERNS = [
    ".DS_Store",
    "__pycache__",
    ".sync_cache.json",  # Our own cache file
]


class TaskModule:
    """
    Module for task system folder sync operations in TerminalUse.

    Provides high-level async methods for:
    - sync_down_system_folder: Download .claude folder from GCS if changed
    - sync_up_system_folder: Upload .claude folder to GCS if changed

    The system folder is synced per-task and stores task-specific state
    like .claude/memory, .claude/config, etc.
    """

    def __init__(
        self,
        client: AsyncTerminalUse | None = None,
    ):
        """
        Initialize task module.

        Args:
            client: Optional TerminalUse client (creates new if not provided)
        """
        self._client = client

    def _get_client(self) -> AsyncTerminalUse:
        """Get or create the TerminalUse client lazily."""
        if self._client is None:
            self._client = create_async_terminaluse_client()
        return self._client

    def _get_local_path(self, task_id: str) -> Path:
        """Get local path for task's system folder."""
        return Path(DATA_ROOT_PATH) / "tasks" / task_id / DOT_CLAUDE_CONFIG["host_path"]

    def _get_cache_path(self, task_id: str) -> str:
        """Get cache file path for task."""
        return f"{DATA_ROOT_PATH}/tasks/{task_id}/.sync_cache.json"

    def _load_cache(self, task_id: str) -> dict:
        """Load cache with atomic read."""
        path = self._get_cache_path(task_id)
        if not os.path.exists(path):
            return {"version": 1, "system_folders": {}}
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load task sync cache: {e}")
            return {"version": 1, "system_folders": {}}

    def _save_cache(self, task_id: str, cache: dict) -> None:
        """Save cache with atomic write."""
        atomic_json_write(self._get_cache_path(task_id), cache)

    def _get_cached_checksum(self, task_id: str, folder_type: str = "dot_claude") -> str | None:
        """Get cached checksum for a folder type."""
        cache = self._load_cache(task_id)
        folder_cache = cache.get("system_folders", {}).get(folder_type, {})
        return folder_cache.get("checksum")

    def _set_cached_checksum(self, task_id: str, folder_type: str, checksum: str | None) -> None:
        """Set cached checksum for a folder type."""
        from datetime import datetime, timezone

        cache = self._load_cache(task_id)
        if "system_folders" not in cache:
            cache["system_folders"] = {}
        cache["system_folders"][folder_type] = {
            "checksum": checksum,
            "last_synced_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_cache(task_id, cache)

    async def sync_down_system_folder(
        self,
        task_id: str,
        folder_type: Literal["dot_claude"] = "dot_claude",
    ) -> SyncDownResult:
        """
        Sync system folder from GCS to local.

        1. Create local directory if needed (required for mount even if GCS empty)
        2. Get remote checksum from GET /tasks/{task_id}/system-folders/dot_claude
        3. Compare with local cache checksum (from internal cache)
        4. If different, get download URL and fetch archive
        5. Extract to local path (or leave empty if GCS has no content)
        6. Update internal cache with new checksum

        Args:
            task_id: ID of the task
            folder_type: Type of system folder (currently only "dot_claude" supported)

        Returns:
            SyncDownResult with sync status
        """
        local_path = self._get_local_path(task_id)

        # Always create local directory for mount (even if GCS is empty)
        try:
            local_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise FilesystemSyncError(f"Failed to create system folder directory {local_path}: {e}") from e

        client = self._get_client()

        # 1. Get local cached checksum
        local_checksum = self._get_cached_checksum(task_id, folder_type)

        # 2. Get remote system folder state
        try:
            system_folder = await client.tasks.get_system_folder(task_id, folder_type)
            if system_folder is None:
                logger.info(f"System folder {folder_type} returned None for task {task_id} - treating as empty")
                return SyncDownResult(folder_type=folder_type, checksum=None, synced=False)
            remote_checksum: str | None = system_folder.archive_checksum
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # System folder doesn't exist yet (new task) - continue with empty
                logger.info(f"System folder {folder_type} not found for task {task_id} - treating as empty")
                return SyncDownResult(folder_type=folder_type, checksum=None, synced=False)
            raise

        # 3. Fast path: unchanged (only skip if we have checksums to compare)
        if remote_checksum is not None and local_checksum == remote_checksum:
            logger.debug(f"System folder {folder_type} for task {task_id} unchanged, skipping download")
            return SyncDownResult(folder_type=folder_type, checksum=remote_checksum, synced=False)

        # 4. Get presigned URL
        url_response = await client.tasks.get_system_folder_download_url(task_id, folder_type)
        if url_response is None or not url_response.url:
            logger.warning(f"No download URL for system folder {folder_type} task {task_id} - treating as empty")
            return SyncDownResult(folder_type=folder_type, checksum=None, synced=False)

        # 5. Download archive - handle 404 as empty folder
        try:
            logger.info(f"Downloading system folder {folder_type} for task {task_id}")
            archive_data = await download_from_presigned_url(url_response.url)
        except FilesystemNotFoundError:
            logger.info(f"System folder {folder_type} archive not found for task {task_id} - treating as empty")
            return SyncDownResult(folder_type=folder_type, checksum=None, synced=False)

        # 6. Extract to local path
        try:
            result = await extract_archive(archive_data, local_path)
            logger.info(f"Extracted {result.files_count} files to {local_path}")
        except CorruptArchiveError as e:
            logger.error(f"Corrupt archive for system folder {folder_type} task {task_id}: {e}")
            raise

        # 7. Update cache with new checksum
        self._set_cached_checksum(task_id, folder_type, remote_checksum)

        return SyncDownResult(folder_type=folder_type, checksum=remote_checksum, synced=True)

    async def sync_up_system_folder(
        self,
        task_id: str,
        folder_type: Literal["dot_claude"] = "dot_claude",
    ) -> SyncUpResult:
        """
        Sync system folder from local to GCS.

        1. Check if local folder exists (skip if not)
        2. Build local archive with checksum
        3. Compare with cached checksum (from internal cache)
        4. If different, get upload URL and push archive
        5. Call sync-complete endpoint
        6. Update internal cache with new checksum

        Args:
            task_id: ID of the task
            folder_type: Type of system folder (currently only "dot_claude" supported)

        Returns:
            SyncUpResult with sync status
        """
        local_path = self._get_local_path(task_id)

        # Check if local folder exists
        if not local_path.exists():
            logger.debug(f"System folder {folder_type} for task {task_id} does not exist locally, skipping upload")
            return SyncUpResult(folder_type=folder_type, checksum="", size_bytes=0)

        # Check if folder is empty
        if not any(local_path.iterdir()):
            logger.debug(f"System folder {folder_type} for task {task_id} is empty, skipping upload")
            return SyncUpResult(folder_type=folder_type, checksum="", size_bytes=0)

        client = self._get_client()

        # 1. Create archive
        logger.info(f"Creating archive for system folder {folder_type} task {task_id}")
        archive_result: ArchiveResult = await create_archive(local_path, SYSTEM_FOLDER_SKIP_PATTERNS)

        # 2. Check if checksum changed
        local_cached_checksum = self._get_cached_checksum(task_id, folder_type)
        if archive_result.checksum == local_cached_checksum:
            logger.debug(f"System folder {folder_type} for task {task_id} unchanged, skipping upload")
            return SyncUpResult(
                folder_type=folder_type,
                checksum=archive_result.checksum,
                size_bytes=archive_result.size_bytes,
            )

        # 3. Get presigned URL
        url_response = await client.tasks.get_system_folder_upload_url(task_id, folder_type)

        # 4. Upload archive
        logger.info(f"Uploading {archive_result.size_bytes} bytes to GCS for system folder {folder_type}")
        await upload_to_presigned_url(url_response.url, archive_result.data)

        # 5. Complete sync
        sync_id = str(uuid.uuid4())
        await self._call_sync_complete(
            task_id=task_id,
            folder_type=folder_type,
            sync_id=sync_id,
            direction="UP",
            status="SUCCESS",
            archive_size_bytes=archive_result.size_bytes,
            archive_checksum=archive_result.checksum,
        )

        # 6. Update cache
        self._set_cached_checksum(task_id, folder_type, archive_result.checksum)

        return SyncUpResult(
            folder_type=folder_type,
            checksum=archive_result.checksum,
            size_bytes=archive_result.size_bytes,
        )

    @retry(stop=SYNC_COMPLETE_RETRY_STOP, wait=SYNC_COMPLETE_RETRY_WAIT, retry=SYNC_COMPLETE_RETRY_CONDITION)
    async def _call_sync_complete(
        self,
        task_id: str,
        folder_type: Literal["dot_claude"],
        sync_id: str,
        direction: str,
        status: str,
        archive_size_bytes: int | None,
        archive_checksum: str | None,
    ) -> None:
        """
        Call POST /tasks/{task_id}/system-folders/{folder_type}/sync-complete via generated SDK with retry.

        Retries once on transient network failures (TimeoutException, ConnectError).
        """
        client = self._get_client()

        await client.tasks.system_folder_sync_complete(
            task_id,
            folder_type,
            sync_id=sync_id,
            direction=direction,
            status=status,
            archive_size_bytes=archive_size_bytes,
            archive_checksum=archive_checksum,
        )


# Singleton instance for ADK usage
task = TaskModule()

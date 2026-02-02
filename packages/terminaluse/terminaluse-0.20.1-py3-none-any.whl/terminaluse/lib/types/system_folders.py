"""
System folder types for TaskModule sync operations.

Note: SystemFolderTypeResponse is already provided by the generated SDK (terminaluse.types).
This module only defines the sync result types used internally by TaskModule.
"""

from pydantic import BaseModel


class SyncDownResult(BaseModel):
    """Result of syncing a system folder from GCS to local."""

    folder_type: str
    checksum: str | None = None  # None if nothing to download (empty or not found)
    synced: bool  # False if already up-to-date (checksums match)


class SyncUpResult(BaseModel):
    """Result of syncing a system folder from local to GCS."""

    folder_type: str
    checksum: str
    size_bytes: int

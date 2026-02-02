"""
Filesystem manifest building with mtime-based dirty detection and caching.

This module provides efficient manifest building for filesystem sync operations,
optimized for the common case where nothing has changed between syncs.
"""

from __future__ import annotations

import os
import json
import asyncio
import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import field, asdict, dataclass
from concurrent.futures import ThreadPoolExecutor

from terminaluse.lib.utils.logging import make_logger
from terminaluse.lib.utils.file_utils import atomic_json_write
from terminaluse.lib.utils.filesystem_archive import should_skip_path

logger = make_logger(__name__)

# Constants
MAX_CONTENT_SIZE = 1_048_576  # 1MB - max file size for content inclusion
MAX_FILE_COUNT = 10_000  # Maximum files in manifest payload
MAX_PAYLOAD_SIZE = 50 * 1024 * 1024  # 50MB - maximum manifest payload size
CACHE_VERSION = 1

# Skip patterns (configurable)
DEFAULT_SKIP_PATTERNS = [
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    ".DS_Store",
    "node_modules",
    ".venv",
    "venv",
    ".sb_manifest_cache.json",  # Legacy cache files
    ".sb_sync_cache.json",  # Legacy cache files
    ".filesystem_sync_cache.json",  # New filesystem sync cache
    ".filesystem_manifest_cache.json",  # New manifest cache
    ".sync_cache.json",  # Task unified cache
    ".sandbox_mounts.json",  # Sandbox mount config (debugging)
]

# Text file detection - MIME type prefixes that indicate text content
TEXT_MIME_PREFIXES = [
    "text/",
    "application/json",
    "application/xml",
    "application/javascript",
    "application/typescript",
    "application/x-yaml",
    "application/toml",
]

# Text file detection - extensions for files without reliable MIME types
TEXT_EXTENSIONS = {
    ".md",
    ".markdown",
    ".rst",
    ".txt",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".json",
    ".jsonl",
    ".json5",
    ".xml",
    ".html",
    ".htm",
    ".xhtml",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".py",
    ".pyi",
    ".pyw",
    ".rb",
    ".rake",
    ".gemspec",
    ".go",
    ".rs",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cc",
    ".java",
    ".kt",
    ".kts",
    ".scala",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".sql",
    ".graphql",
    ".gql",
    ".env",
    ".env.example",
    ".env.local",
    ".gitignore",
    ".gitattributes",
    ".dockerignore",
    ".editorconfig",
    ".prettierrc",
    ".eslintrc",
    # Handle files without extension like Makefile, Dockerfile
}

# Files without extensions that are text
TEXT_FILES_NO_EXT = {
    "makefile",
    "dockerfile",
    "procfile",
    "gemfile",
    "rakefile",
    "vagrantfile",
    "jenkinsfile",
    "readme",
    "license",
    "changelog",
    "contributing",
    "authors",
}


@dataclass
class CachedFileEntry:
    """Cached metadata for a single file."""

    mtime: float  # os.stat st_mtime
    size: int  # os.stat st_size
    checksum: str  # SHA256 hex
    content: str | None  # UTF-8 content if text & ≤1MB
    mime_type: str | None
    is_binary: bool
    content_truncated: bool = False


@dataclass
class ManifestEntry:
    """File entry for sync-complete API."""

    path: str
    is_directory: bool
    size_bytes: int | None
    checksum: str | None
    mime_type: str | None
    modified_at: datetime
    content: str | None
    is_binary: bool
    content_truncated: bool = False


@dataclass
class ManifestResult:
    """Result of manifest building."""

    is_dirty: bool
    entries: list[ManifestEntry]
    from_cache: bool


class ManifestTooLargeError(Exception):
    """Raised when filesystem exceeds file count or payload size limits."""

    def __init__(self, file_count: int, payload_size: int):
        self.file_count = file_count
        self.payload_size = payload_size
        super().__init__(
            f"Filesystem too large: {file_count} files, {payload_size / 1024 / 1024:.1f}MB. "
            f"Limits: {MAX_FILE_COUNT} files, {MAX_PAYLOAD_SIZE / 1024 / 1024:.0f}MB. "
            "Add patterns to skip to reduce filesystem size."
        )


def _is_text_file(file_path: Path, content: bytes) -> bool:
    """
    Determine if file is text.

    Strategy:
    1. Check extension against TEXT_EXTENSIONS (fast, no I/O)
    2. Check filename (without extension) against TEXT_FILES_NO_EXT
    3. Check MIME type against TEXT_MIME_PREFIXES (fast)
    4. Check for null bytes in first 8KB (reliable fallback)

    Returns True if text, False if binary.
    """
    # Fast path: check extension
    suffix = file_path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return True

    # Check filename without extension (for Makefile, Dockerfile, etc.)
    name_lower = file_path.name.lower()
    if name_lower in TEXT_FILES_NO_EXT:
        return True

    # Check MIME type
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type:
        if any(mime_type.startswith(prefix) for prefix in TEXT_MIME_PREFIXES):
            return True

    # Fallback: check for null bytes in first 8KB
    sample = content[:8192]
    return b"\x00" not in sample


def _process_single_file(
    file_path: Path,
    rel_path: str,
) -> tuple[str, CachedFileEntry]:
    """
    Process a single file synchronously (runs in thread pool).

    Returns (rel_path, CachedFileEntry) tuple.
    """
    stat = file_path.stat()
    content_bytes = file_path.read_bytes()

    # Determine if binary
    is_binary = not _is_text_file(file_path, content_bytes)

    # Get MIME type
    mime_type, _ = mimetypes.guess_type(str(file_path))

    # Extract text content if applicable
    text_content: str | None = None
    content_truncated = False

    if not is_binary:
        try:
            if len(content_bytes) <= MAX_CONTENT_SIZE:
                text_content = content_bytes.decode("utf-8")
            else:
                text_content = content_bytes[:MAX_CONTENT_SIZE].decode("utf-8", errors="ignore")
                content_truncated = True
        except UnicodeDecodeError:
            is_binary = True

    return rel_path, CachedFileEntry(
        mtime=stat.st_mtime,
        size=stat.st_size,
        checksum=hashlib.sha256(content_bytes).hexdigest(),
        content=text_content,
        mime_type=mime_type,
        is_binary=is_binary,
        content_truncated=content_truncated,
    )


@dataclass
class ManifestCache:
    """Persistent cache for manifest entries."""

    version: int = CACHE_VERSION
    entries: dict[str, CachedFileEntry] = field(default_factory=dict)


class SyncCache:
    """
    Tracks last sync state for checksum comparison.

    File: .filesystem_sync_cache.json
    Contents: { "archive_checksum": "sha256:...", "last_synced_at": "..." }
    """

    def __init__(self, local_path: Path):
        self.cache_file = local_path / ".filesystem_sync_cache.json"
        self._data: dict[str, str | None] = {}
        self._load()

    def get_archive_checksum(self) -> str | None:
        """Get last known archive checksum."""
        return self._data.get("archive_checksum")

    def set_archive_checksum(self, checksum: str) -> None:
        """Update archive checksum and save."""
        self._data["archive_checksum"] = checksum
        self._data["last_synced_at"] = datetime.now(timezone.utc).isoformat()
        self._save()

    def _load(self) -> None:
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                self._data = json.loads(self.cache_file.read_text())
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load sync cache: {e}")
                self._data = {}

    def _save(self) -> None:
        """Save cache to file using atomic write."""
        try:
            atomic_json_write(str(self.cache_file), self._data)
        except OSError as e:
            logger.warning(f"Failed to save sync cache: {e}")


class FilesystemManifest:
    """
    Incremental manifest builder with mtime-based dirty detection.

    Optimizations:
    1. Stat-only first pass to detect changes
    2. Only hash/read changed files
    3. Persist cache for next request
    """

    def __init__(self, local_path: Path, skip_patterns: list[str] | None = None):
        self.local_path = local_path.resolve()
        self.skip_patterns = skip_patterns or DEFAULT_SKIP_PATTERNS
        self.cache_file = local_path / ".filesystem_manifest_cache.json"
        self._cache: dict[str, CachedFileEntry] = {}
        self._load_cache()

    def _should_skip(self, path: Path) -> bool:
        """Check if path matches skip patterns."""
        return should_skip_path(path, self.skip_patterns)

    async def check_dirty_and_build(self) -> ManifestResult:
        """
        Single-pass dirty detection and manifest building (async).

        Runs file I/O in a thread pool to avoid blocking the event loop.

        Algorithm:
        1. Stat scan all files, compare mtime/size to cache
        2. If no changes, return cached manifest (fast path)
        3. For changed files only: read, hash, detect binary, get content
        4. Update cache and save
        5. Return full manifest from cache

        Returns ManifestResult with is_dirty flag
        """
        return await asyncio.to_thread(self._check_dirty_and_build_sync)

    def _check_dirty_and_build_sync(self) -> ManifestResult:
        """
        Synchronous implementation of dirty detection and manifest building.

        Called via asyncio.to_thread() from check_dirty_and_build().
        """
        current_files: dict[str, tuple[float, int]] = {}  # path -> (mtime, size)
        changed_files: list[tuple[str, Path]] = []

        # Phase 1: Quick stat scan - O(n) stats, very fast
        for file_path in self.local_path.rglob("*"):
            if not file_path.is_file():
                continue

            # Get relative path
            try:
                rel_path = str(file_path.relative_to(self.local_path))
            except ValueError:
                continue

            # Check skip patterns
            if self._should_skip(Path(rel_path)):
                continue

            try:
                stat = file_path.stat()
                current_files[rel_path] = (stat.st_mtime, stat.st_size)

                # Check if file is new or modified
                cached = self._cache.get(rel_path)
                if cached is None or cached.mtime != stat.st_mtime or cached.size != stat.st_size:
                    changed_files.append((rel_path, file_path))
            except OSError as e:
                logger.warning(f"Failed to stat file {rel_path}: {e}")
                continue

        # Check for deleted files
        deleted_files = set(self._cache.keys()) - set(current_files.keys())

        # Fast path: nothing changed - return cached manifest
        if not changed_files and not deleted_files:
            return ManifestResult(
                is_dirty=False,
                entries=self._build_manifest_from_cache(),
                from_cache=True,
            )

        # Phase 2: Process only changed files
        if len(changed_files) > 100:
            # Use parallel processing for large changesets
            self._process_files_parallel(changed_files)
        else:
            # Sequential processing for small changesets
            for rel_path, file_path in changed_files:
                try:
                    _, entry = _process_single_file(file_path, rel_path)
                    self._cache[rel_path] = entry
                except (OSError, PermissionError) as e:
                    logger.warning(f"Failed to process file {rel_path}: {e}")
                    continue

        # Remove deleted files from cache
        for rel_path in deleted_files:
            del self._cache[rel_path]

        # Persist cache for next request
        self._save_cache()

        # Build full manifest from cache
        return ManifestResult(
            is_dirty=True,
            entries=self._build_manifest_from_cache(),
            from_cache=False,
        )

    def _process_files_parallel(
        self,
        changed_files: list[tuple[str, Path]],
        max_workers: int | None = None,
    ) -> None:
        """Process multiple files in parallel."""
        if max_workers is None:
            # 3x CPU cores is optimal for mixed I/O + hashing workloads
            max_workers = (os.cpu_count() or 1) * 3

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(_process_single_file, file_path, rel_path) for rel_path, file_path in changed_files
            ]
            for future in futures:
                try:
                    rel_path, entry = future.result()
                    self._cache[rel_path] = entry
                except Exception as e:
                    logger.warning(f"Failed to process file in parallel: {e}")

    def _build_manifest_from_cache(self) -> list[ManifestEntry]:
        """Build manifest entries from cache."""
        entries: list[ManifestEntry] = []
        for path, cached in self._cache.items():
            entries.append(
                ManifestEntry(
                    path=path,
                    is_directory=False,
                    size_bytes=cached.size,
                    checksum=f"sha256:{cached.checksum}",
                    mime_type=cached.mime_type,
                    modified_at=datetime.fromtimestamp(cached.mtime, tz=timezone.utc),
                    content=cached.content,
                    is_binary=cached.is_binary,
                    content_truncated=cached.content_truncated,
                )
            )
        return entries

    def get_cached_manifest(self) -> list[ManifestEntry]:
        """Return manifest from cache without scanning."""
        return self._build_manifest_from_cache()

    def _load_cache(self) -> None:
        """Load cache from .filesystem_manifest_cache.json"""
        if not self.cache_file.exists():
            return

        try:
            data = json.loads(self.cache_file.read_text())
            # Check version
            if data.get("version") != CACHE_VERSION:
                logger.info("Cache version mismatch, rebuilding")
                return

            # Load entries
            for path, entry_data in data.get("entries", {}).items():
                self._cache[path] = CachedFileEntry(
                    mtime=entry_data["mtime"],
                    size=entry_data["size"],
                    checksum=entry_data["checksum"],
                    content=entry_data.get("content"),
                    mime_type=entry_data.get("mime_type"),
                    is_binary=entry_data.get("is_binary", False),
                    content_truncated=entry_data.get("content_truncated", False),
                )
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"Failed to load manifest cache: {e}")
            self._cache = {}

    def _save_cache(self) -> None:
        """Save cache to .filesystem_manifest_cache.json using atomic write."""
        try:
            data = {
                "version": CACHE_VERSION,
                "entries": {path: asdict(entry) for path, entry in self._cache.items()},
            }
            atomic_json_write(str(self.cache_file), data)
        except OSError as e:
            logger.warning(f"Failed to save manifest cache: {e}")


def validate_manifest_size(entries: list[ManifestEntry]) -> None:
    """
    Validate manifest doesn't exceed size limits.

    Raises:
        ManifestTooLargeError: If limits exceeded
    """
    file_count = len(entries)

    # Calculate approximate payload size
    payload_size = sum(
        len(e.path.encode("utf-8"))
        + (len(e.content.encode("utf-8")) if e.content else 0)
        + (len(e.checksum) if e.checksum else 0)
        + 100  # Overhead for JSON structure
        for e in entries
    )

    if file_count > MAX_FILE_COUNT:
        raise ManifestTooLargeError(file_count, payload_size)

    if payload_size > MAX_PAYLOAD_SIZE:
        raise ManifestTooLargeError(file_count, payload_size)

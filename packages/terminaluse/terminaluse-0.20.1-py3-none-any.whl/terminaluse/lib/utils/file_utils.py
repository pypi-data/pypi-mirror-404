"""File utilities for atomic operations."""

import json
import os
from typing import Any


def atomic_json_write(path: str, data: Any, indent: int = 2) -> None:
    """Write JSON atomically using temp file + rename.

    Prevents cache corruption on crash or concurrent access.

    Args:
        path: Target file path
        data: JSON-serializable data to write
        indent: JSON indentation level (default: 2)
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = f"{path}.tmp"
    with open(temp_path, "w") as f:
        json.dump(data, f, indent=indent)
    os.rename(temp_path, path)  # Atomic on POSIX

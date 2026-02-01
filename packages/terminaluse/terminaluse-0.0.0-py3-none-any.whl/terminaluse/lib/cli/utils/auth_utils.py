from __future__ import annotations

import json
import base64
from typing import Any, Dict

from terminaluse.lib.sdk.config.agent_manifest import AgentManifest


def _encode_principal_context(manifest: AgentManifest) -> str | None:  # noqa: ARG001
    """
    Encode principal context from manifest.

    Note: Auth is now handled by the platform. This function returns None
    for local development compatibility.
    """
    # Auth is handled by platform - no manifest-based auth
    return None


def _encode_principal_dict(principal: Dict[str, Any]) -> str | None:
    """
    Encode principal dictionary directly.

    Args:
        principal: Dictionary containing principal configuration

    Returns:
        Base64-encoded JSON string of the principal, or None if principal is empty
    """
    if not principal:
        return None

    json_str = json.dumps(principal, separators=(",", ":"))
    encoded_bytes = base64.b64encode(json_str.encode("utf-8"))
    return encoded_bytes.decode("utf-8")

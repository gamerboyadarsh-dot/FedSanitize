"""
Deterministic hashing utilities for the tamper-evident audit chain.

Design note: this makes the chain *tamper-evident*, not tamper-proof or
immutable. Anyone with write access to the underlying storage file/DB can
still edit it; what the hash chain guarantees is that such an edit will be
detectable by verify_chain(). Docs/UI copy should say "tamper-evident",
never "impossible to modify".
"""

import hashlib
import json
from typing import Any

GENESIS_HASH = "0" * 64


def safe_serializer(obj: Any) -> Any:
    """Fallback for json.dumps on objects that aren't natively serializable."""
    try:
        return str(obj)
    except Exception:
        return "<unserializable>"


def canonical_json(data: dict) -> bytes:
    """Deterministic (sorted-key, no-whitespace) JSON encoding."""
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        default=safe_serializer,
    ).encode("utf-8")


def compute_hash(event_content: dict) -> str:
    """
    event_content must already include `previous_hash` (see
    AuditEvent.content_for_hash) so the chain link is baked into the hash.
    """
    blob = canonical_json(event_content)
    return hashlib.sha256(blob).hexdigest()

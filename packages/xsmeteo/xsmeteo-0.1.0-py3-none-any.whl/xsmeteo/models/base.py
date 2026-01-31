from __future__ import annotations

import msgspec


class BaseStruct(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """Base immutable structure for all API models.

    Enforces:
    - Keyword-only arguments
    - Forbids unknown fields (strict schema)
    """

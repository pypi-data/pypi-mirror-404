"""
Common definitions for services.
"""

from __future__ import annotations

import dataclasses
import typing

if typing.TYPE_CHECKING:
    from typing import TypeVar

    T = TypeVar("T")


@dataclasses.dataclass
class RequestDef[T]:
    """Definition of an API request."""

    url: str
    params: dict[str, typing.Any]
    model: type[T]

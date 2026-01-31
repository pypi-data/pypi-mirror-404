# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

__all__ = ["RequestGetParams"]


class RequestGetParams(TypedDict, total=False):
    request_id: Required[Optional[str]]
    """which is returned by add_memories api"""

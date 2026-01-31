# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from ..._models import BaseModel

__all__ = ["MemoryDeleteResponse", "Result"]


class Result(BaseModel):
    """Delete operation result"""

    count: Optional[int] = None
    """Number of memories deleted"""

    filters: Optional[List[str]] = None
    """List of filter types used for deletion"""


class MemoryDeleteResponse(BaseModel):
    result: Result
    """Delete operation result"""

    message: Optional[str] = None
    """Response message"""

    status: Optional[str] = None
    """Response status"""

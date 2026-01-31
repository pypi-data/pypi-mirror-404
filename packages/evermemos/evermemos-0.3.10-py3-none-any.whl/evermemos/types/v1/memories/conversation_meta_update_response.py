# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from ...._models import BaseModel

__all__ = ["ConversationMetaUpdateResponse", "Result"]


class Result(BaseModel):
    """Patch result with updated fields"""

    id: str
    """Document ID"""

    group_id: Optional[str] = None
    """Group ID (null for default config)"""

    name: Optional[str] = None
    """Conversation name"""

    scene: Optional[str] = None
    """Scene identifier"""

    updated_at: Optional[str] = None
    """Record update time"""

    updated_fields: Optional[List[str]] = None
    """List of updated field names"""


class ConversationMetaUpdateResponse(BaseModel):
    result: Result
    """Patch result with updated fields"""

    message: Optional[str] = None
    """Response message"""

    status: Optional[str] = None
    """Response status"""

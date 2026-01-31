# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

from ..._types import SequenceNotStr

__all__ = ["MemoryAddParams"]


class MemoryAddParams(TypedDict, total=False):
    content: Required[str]
    """Message content"""

    create_time: Required[str]
    """Message creation time (ISO 8601 format)"""

    message_id: Required[str]
    """Message unique identifier"""

    sender: Required[str]
    """Sender user ID (required).

    Also used as user_id internally for memory ownership.
    """

    flush: bool
    """Force boundary trigger.

    When True, immediately triggers memory extraction instead of waiting for natural
    boundary detection.
    """

    group_id: Optional[str]
    """Group ID.

    If not provided, will automatically generate based on hash(sender) + '\\__group'
    suffix, representing single-user mode where each user's messages are extracted
    into separate memory spaces.
    """

    group_name: Optional[str]
    """Group name"""

    refer_list: Optional[SequenceNotStr[str]]
    """List of referenced message IDs"""

    role: Optional[str]
    """
    Message sender role, used to identify the source of the message. Enum values
    from MessageSenderRole:

    - user: Message from a human user
    - assistant: Message from an AI assistant
    """

    sender_name: Optional[str]
    """Sender name (uses sender if not provided)"""

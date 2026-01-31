# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Required, TypedDict

from ...._types import SequenceNotStr

__all__ = [
    "ConversationMetaUpdateParams",
    "LlmCustomSetting",
    "LlmCustomSettingBoundary",
    "LlmCustomSettingExtraction",
    "UserDetails",
]


class ConversationMetaUpdateParams(TypedDict, total=False):
    default_timezone: Optional[str]
    """New default timezone"""

    description: Optional[str]
    """New description"""

    group_id: Optional[str]
    """Group ID to update. When null, updates the global (default) config."""

    llm_custom_setting: Optional[LlmCustomSetting]
    """New LLM custom settings.

    **Only allowed for global config (group_id=null). Not allowed for group config
    (inherited from global config).**
    """

    name: Optional[str]
    """New group/conversation name.

    **Only allowed for group config (group_id provided). Not allowed for global
    config.**
    """

    scene_desc: Optional[Dict[str, object]]
    """New scene description.

    **Only allowed for global config (group_id=null). Not allowed for group config
    (inherited from global config).**
    """

    tags: Optional[SequenceNotStr[str]]
    """New tag list"""

    user_details: Optional[Dict[str, UserDetails]]
    """New user details (will completely replace existing user_details)"""


class LlmCustomSettingBoundary(TypedDict, total=False):
    """LLM config for boundary detection (fast, cheap model recommended)"""

    model: Required[str]
    """Model name"""

    provider: Required[str]
    """LLM provider name"""

    extra: Optional[Dict[str, object]]
    """Additional provider-specific configuration"""


class LlmCustomSettingExtraction(TypedDict, total=False):
    """LLM config for memory extraction (high quality model recommended)"""

    model: Required[str]
    """Model name"""

    provider: Required[str]
    """LLM provider name"""

    extra: Optional[Dict[str, object]]
    """Additional provider-specific configuration"""


class LlmCustomSetting(TypedDict, total=False):
    """New LLM custom settings.

    **Only allowed for global config (group_id=null).
    Not allowed for group config (inherited from global config).**
    """

    boundary: Optional[LlmCustomSettingBoundary]
    """LLM config for boundary detection (fast, cheap model recommended)"""

    extra: Optional[Dict[str, object]]
    """Additional task-specific LLM configurations"""

    extraction: Optional[LlmCustomSettingExtraction]
    """LLM config for memory extraction (high quality model recommended)"""


class UserDetails(TypedDict, total=False):
    custom_role: Optional[str]
    """User's job/position role (e.g. developer, designer, manager)"""

    extra: Optional[Dict[str, object]]
    """Additional information"""

    full_name: Optional[str]
    """User full name"""

    role: Optional[str]
    """
    User type role, used to identify if this user is a human or AI. Enum values from
    MessageSenderRole:

    - user: Human user
    - assistant: AI assistant/bot
    """

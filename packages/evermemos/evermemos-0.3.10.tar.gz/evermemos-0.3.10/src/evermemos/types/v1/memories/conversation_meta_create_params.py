# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Required, TypedDict

from ...._types import SequenceNotStr

__all__ = [
    "ConversationMetaCreateParams",
    "LlmCustomSetting",
    "LlmCustomSettingBoundary",
    "LlmCustomSettingExtraction",
    "UserDetails",
]


class ConversationMetaCreateParams(TypedDict, total=False):
    created_at: Required[str]
    """Conversation creation time (ISO 8601 format)"""

    default_timezone: Optional[str]
    """Default timezone"""

    description: Optional[str]
    """Conversation description"""

    group_id: Optional[str]
    """Group unique identifier.

    When null/not provided, represents default settings for this scene.
    """

    llm_custom_setting: Optional[LlmCustomSetting]
    """LLM custom settings for algorithm control.

    **Only for global config (group_id=null), not allowed for group config (group_id
    provided).**

    Allows configuring different LLM providers/models for different tasks like
    boundary detection and memory extraction.
    """

    name: Optional[str]
    """Group/conversation name.

    **Required for group config (group_id provided), not allowed for global config
    (group_id=null).**
    """

    scene: Optional[str]
    """Scene identifier.

    **Required for global config (group_id=null), not allowed for group config
    (group_id provided).**

    Enum values from ScenarioType:

    - group_chat: work/group chat scenario, suitable for group conversations such as
      multi-person collaboration and project discussions
    - assistant: assistant scenario, suitable for one-on-one AI assistant
      conversations
    """

    scene_desc: Optional[Dict[str, object]]
    """Scene description object.

    **Required for global config (group_id=null), not allowed for group config
    (group_id provided).**

    Can include fields like description, type, etc.
    """

    tags: Optional[SequenceNotStr[str]]
    """Tag list"""

    user_details: Optional[Dict[str, UserDetails]]
    """Participant details, key is user ID, value is user detail object"""


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
    """LLM custom settings for algorithm control.

    **Only for global config (group_id=null),
    not allowed for group config (group_id provided).**

    Allows configuring different LLM providers/models for different tasks like boundary detection and memory extraction.
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

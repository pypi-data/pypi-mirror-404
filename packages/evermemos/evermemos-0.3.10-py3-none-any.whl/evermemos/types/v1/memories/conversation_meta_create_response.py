# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional

from ...._models import BaseModel

__all__ = [
    "ConversationMetaCreateResponse",
    "Result",
    "ResultLlmCustomSetting",
    "ResultLlmCustomSettingBoundary",
    "ResultLlmCustomSettingExtraction",
]


class ResultLlmCustomSettingBoundary(BaseModel):
    """LLM config for boundary detection (fast, cheap model recommended)"""

    model: str
    """Model name"""

    provider: str
    """LLM provider name"""

    extra: Optional[Dict[str, object]] = None
    """Additional provider-specific configuration"""


class ResultLlmCustomSettingExtraction(BaseModel):
    """LLM config for memory extraction (high quality model recommended)"""

    model: str
    """Model name"""

    provider: str
    """LLM provider name"""

    extra: Optional[Dict[str, object]] = None
    """Additional provider-specific configuration"""


class ResultLlmCustomSetting(BaseModel):
    """LLM custom settings (only for global config)"""

    boundary: Optional[ResultLlmCustomSettingBoundary] = None
    """LLM config for boundary detection (fast, cheap model recommended)"""

    extra: Optional[Dict[str, object]] = None
    """Additional task-specific LLM configurations"""

    extraction: Optional[ResultLlmCustomSettingExtraction] = None
    """LLM config for memory extraction (high quality model recommended)"""


class Result(BaseModel):
    """Saved conversation metadata"""

    id: str
    """Document ID"""

    conversation_created_at: Optional[str] = None
    """Conversation creation time"""

    created_at: Optional[str] = None
    """Record creation time"""

    default_timezone: Optional[str] = None
    """Default timezone"""

    description: Optional[str] = None
    """Description"""

    group_id: Optional[str] = None
    """Group ID (null for global config)"""

    is_default: Optional[bool] = None
    """Whether this is the global (default) config"""

    llm_custom_setting: Optional[ResultLlmCustomSetting] = None
    """LLM custom settings (only for global config)"""

    name: Optional[str] = None
    """Group/conversation name (only for group config)"""

    scene: Optional[str] = None
    """Scene identifier (only for global config)"""

    scene_desc: Optional[Dict[str, object]] = None
    """Scene description (only for global config)"""

    tags: Optional[List[str]] = None
    """Tags"""

    updated_at: Optional[str] = None
    """Record update time"""

    user_details: Optional[Dict[str, Dict[str, object]]] = None
    """User details"""


class ConversationMetaCreateResponse(BaseModel):
    result: Result
    """Saved conversation metadata"""

    message: Optional[str] = None
    """Response message"""

    status: Optional[str] = None
    """Response status"""

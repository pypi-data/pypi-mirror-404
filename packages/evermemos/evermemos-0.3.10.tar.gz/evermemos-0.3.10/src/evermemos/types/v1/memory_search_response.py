# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal

from .metadata import Metadata
from ..._models import BaseModel
from .memory_type import MemoryType

__all__ = ["MemorySearchResponse", "Result", "ResultMemory", "ResultPendingMessage"]


class ResultMemory(BaseModel):
    memory_type: MemoryType

    ori_event_id_list: List[str]

    timestamp: datetime

    user_id: str

    id: Optional[str] = None

    extend: Optional[Dict[str, object]] = None

    group_id: Optional[str] = None

    group_name: Optional[str] = None

    keywords: Optional[List[str]] = None

    linked_entities: Optional[List[str]] = None

    memcell_event_id_list: Optional[List[str]] = None

    participants: Optional[List[str]] = None

    type: Optional[Literal["Conversation"]] = None

    user_name: Optional[str] = None

    vector: Optional[List[float]] = None

    vector_model: Optional[str] = None


class ResultPendingMessage(BaseModel):
    id: str

    request_id: str

    content: Optional[str] = None

    created_at: Optional[str] = None

    group_id: Optional[str] = None

    group_name: Optional[str] = None

    message_create_time: Optional[str] = None

    message_id: Optional[str] = None

    refer_list: Optional[List[str]] = None

    sender: Optional[str] = None

    sender_name: Optional[str] = None

    updated_at: Optional[str] = None

    user_id: Optional[str] = None


class Result(BaseModel):
    """Memory search result"""

    has_more: Optional[bool] = None

    memories: Optional[List[ResultMemory]] = None

    metadata: Optional[Metadata] = None

    original_data: Optional[List[Dict[str, object]]] = None

    pending_messages: Optional[List[ResultPendingMessage]] = None

    query_metadata: Optional[Metadata] = None

    scores: Optional[List[float]] = None

    total_count: Optional[int] = None


class MemorySearchResponse(BaseModel):
    result: Result
    """Memory search result"""

    message: Optional[str] = None
    """Response message"""

    status: Optional[str] = None
    """Response status"""

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime
from typing_extensions import TypeAlias

from .metadata import Metadata
from ..._models import BaseModel

__all__ = [
    "MemoryGetResponse",
    "Result",
    "ResultMemory",
    "ResultMemoryProfileModel",
    "ResultMemoryGlobalUserProfileModel",
    "ResultMemoryCombinedProfileModel",
    "ResultMemoryCombinedProfileModelGlobalProfile",
    "ResultMemoryCombinedProfileModelProfile",
    "ResultMemoryEpisodicMemoryModel",
    "ResultMemoryEventLogModel",
    "ResultMemoryForesightModel",
]


class ResultMemoryProfileModel(BaseModel):
    id: str

    group_id: str

    user_id: str

    cluster_ids: Optional[List[str]] = None

    confidence: Optional[float] = None

    created_at: Optional[datetime] = None

    last_updated_cluster: Optional[str] = None

    memcell_count: Optional[int] = None

    profile_data: Optional[Dict[str, object]] = None

    scenario: Optional[str] = None

    updated_at: Optional[datetime] = None

    version: Optional[int] = None


class ResultMemoryGlobalUserProfileModel(BaseModel):
    id: str

    user_id: str

    confidence: Optional[float] = None

    created_at: Optional[datetime] = None

    custom_profile_data: Optional[Dict[str, object]] = None

    memcell_count: Optional[int] = None

    profile_data: Optional[Dict[str, object]] = None

    updated_at: Optional[datetime] = None


class ResultMemoryCombinedProfileModelGlobalProfile(BaseModel):
    id: str

    user_id: str

    confidence: Optional[float] = None

    created_at: Optional[datetime] = None

    custom_profile_data: Optional[Dict[str, object]] = None

    memcell_count: Optional[int] = None

    profile_data: Optional[Dict[str, object]] = None

    updated_at: Optional[datetime] = None


class ResultMemoryCombinedProfileModelProfile(BaseModel):
    id: str

    group_id: str

    user_id: str

    cluster_ids: Optional[List[str]] = None

    confidence: Optional[float] = None

    created_at: Optional[datetime] = None

    last_updated_cluster: Optional[str] = None

    memcell_count: Optional[int] = None

    profile_data: Optional[Dict[str, object]] = None

    scenario: Optional[str] = None

    updated_at: Optional[datetime] = None

    version: Optional[int] = None


class ResultMemoryCombinedProfileModel(BaseModel):
    user_id: str

    global_profile: Optional[ResultMemoryCombinedProfileModelGlobalProfile] = None

    group_id: Optional[str] = None

    profiles: Optional[List[ResultMemoryCombinedProfileModelProfile]] = None


class ResultMemoryEpisodicMemoryModel(BaseModel):
    id: str

    episode_id: str

    user_id: str

    created_at: Optional[datetime] = None

    end_time: Optional[datetime] = None

    episode: Optional[str] = None

    extend: Optional[Dict[str, object]] = None

    group_id: Optional[str] = None

    group_name: Optional[str] = None

    keywords: Optional[List[str]] = None

    location: Optional[str] = None

    metadata: Optional[Metadata] = None

    parent_id: Optional[str] = None

    parent_type: Optional[str] = None

    participants: Optional[List[str]] = None

    start_time: Optional[datetime] = None

    subject: Optional[str] = None

    summary: Optional[str] = None

    timestamp: Optional[datetime] = None

    updated_at: Optional[datetime] = None


class ResultMemoryEventLogModel(BaseModel):
    id: str

    atomic_fact: str

    parent_id: str

    parent_type: str

    timestamp: datetime

    user_id: str

    created_at: Optional[datetime] = None

    event_type: Optional[str] = None

    extend: Optional[Dict[str, object]] = None

    group_id: Optional[str] = None

    group_name: Optional[str] = None

    metadata: Optional[Metadata] = None

    participants: Optional[List[str]] = None

    updated_at: Optional[datetime] = None

    user_name: Optional[str] = None

    vector: Optional[List[float]] = None

    vector_model: Optional[str] = None


class ResultMemoryForesightModel(BaseModel):
    id: str

    content: str

    foresight: str

    parent_id: str

    parent_type: str

    created_at: Optional[datetime] = None

    duration_days: Optional[int] = None

    end_time: Optional[str] = None

    evidence: Optional[str] = None

    extend: Optional[Dict[str, object]] = None

    group_id: Optional[str] = None

    group_name: Optional[str] = None

    metadata: Optional[Metadata] = None

    participants: Optional[List[str]] = None

    start_time: Optional[str] = None

    updated_at: Optional[datetime] = None

    user_id: Optional[str] = None

    user_name: Optional[str] = None

    vector: Optional[List[float]] = None

    vector_model: Optional[str] = None


ResultMemory: TypeAlias = Union[
    ResultMemoryProfileModel,
    ResultMemoryGlobalUserProfileModel,
    ResultMemoryCombinedProfileModel,
    ResultMemoryEpisodicMemoryModel,
    ResultMemoryEventLogModel,
    ResultMemoryForesightModel,
]


class Result(BaseModel):
    """Memory fetch result"""

    has_more: Optional[bool] = None

    memories: Optional[List[ResultMemory]] = None

    metadata: Optional[Metadata] = None

    total_count: Optional[int] = None


class MemoryGetResponse(BaseModel):
    result: Result
    """Memory fetch result"""

    message: Optional[str] = None
    """Response message"""

    status: Optional[str] = None
    """Response status"""

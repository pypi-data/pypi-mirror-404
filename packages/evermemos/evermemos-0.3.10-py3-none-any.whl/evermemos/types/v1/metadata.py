# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["Metadata"]


class Metadata(BaseModel):
    memory_type: str

    source: str

    user_id: str

    email: Optional[str] = None

    full_name: Optional[str] = None

    group_id: Optional[str] = None

    limit: Optional[int] = None

    phone: Optional[str] = None

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from ...._models import BaseModel

__all__ = ["RequestGetResponse"]


class RequestGetResponse(BaseModel):
    success: bool
    """Whether the query was successful"""

    data: Optional[Dict[str, object]] = None
    """Request status data"""

    found: Optional[bool] = None
    """Whether the request status was found"""

    message: Optional[str] = None
    """Message"""

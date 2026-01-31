# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .request import (
    RequestResource,
    AsyncRequestResource,
    RequestResourceWithRawResponse,
    AsyncRequestResourceWithRawResponse,
    RequestResourceWithStreamingResponse,
    AsyncRequestResourceWithStreamingResponse,
)
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource

__all__ = ["StatusResource", "AsyncStatusResource"]


class StatusResource(SyncAPIResource):
    @cached_property
    def request(self) -> RequestResource:
        return RequestResource(self._client)

    @cached_property
    def with_raw_response(self) -> StatusResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/evermemos/evermemos-python#accessing-raw-response-data-eg-headers
        """
        return StatusResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> StatusResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/evermemos/evermemos-python#with_streaming_response
        """
        return StatusResourceWithStreamingResponse(self)


class AsyncStatusResource(AsyncAPIResource):
    @cached_property
    def request(self) -> AsyncRequestResource:
        return AsyncRequestResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncStatusResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/evermemos/evermemos-python#accessing-raw-response-data-eg-headers
        """
        return AsyncStatusResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncStatusResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/evermemos/evermemos-python#with_streaming_response
        """
        return AsyncStatusResourceWithStreamingResponse(self)


class StatusResourceWithRawResponse:
    def __init__(self, status: StatusResource) -> None:
        self._status = status

    @cached_property
    def request(self) -> RequestResourceWithRawResponse:
        return RequestResourceWithRawResponse(self._status.request)


class AsyncStatusResourceWithRawResponse:
    def __init__(self, status: AsyncStatusResource) -> None:
        self._status = status

    @cached_property
    def request(self) -> AsyncRequestResourceWithRawResponse:
        return AsyncRequestResourceWithRawResponse(self._status.request)


class StatusResourceWithStreamingResponse:
    def __init__(self, status: StatusResource) -> None:
        self._status = status

    @cached_property
    def request(self) -> RequestResourceWithStreamingResponse:
        return RequestResourceWithStreamingResponse(self._status.request)


class AsyncStatusResourceWithStreamingResponse:
    def __init__(self, status: AsyncStatusResource) -> None:
        self._status = status

    @cached_property
    def request(self) -> AsyncRequestResourceWithStreamingResponse:
        return AsyncRequestResourceWithStreamingResponse(self._status.request)

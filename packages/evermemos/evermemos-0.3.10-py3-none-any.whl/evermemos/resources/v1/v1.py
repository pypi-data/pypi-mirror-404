# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from .status.status import (
    StatusResource,
    AsyncStatusResource,
    StatusResourceWithRawResponse,
    AsyncStatusResourceWithRawResponse,
    StatusResourceWithStreamingResponse,
    AsyncStatusResourceWithStreamingResponse,
)
from .memories.memories import (
    MemoriesResource,
    AsyncMemoriesResource,
    MemoriesResourceWithRawResponse,
    AsyncMemoriesResourceWithRawResponse,
    MemoriesResourceWithStreamingResponse,
    AsyncMemoriesResourceWithStreamingResponse,
)

__all__ = ["V1Resource", "AsyncV1Resource"]


class V1Resource(SyncAPIResource):
    @cached_property
    def memories(self) -> MemoriesResource:
        return MemoriesResource(self._client)

    @cached_property
    def status(self) -> StatusResource:
        return StatusResource(self._client)

    @cached_property
    def with_raw_response(self) -> V1ResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/evermemos/evermemos-python#accessing-raw-response-data-eg-headers
        """
        return V1ResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> V1ResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/evermemos/evermemos-python#with_streaming_response
        """
        return V1ResourceWithStreamingResponse(self)


class AsyncV1Resource(AsyncAPIResource):
    @cached_property
    def memories(self) -> AsyncMemoriesResource:
        return AsyncMemoriesResource(self._client)

    @cached_property
    def status(self) -> AsyncStatusResource:
        return AsyncStatusResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncV1ResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/evermemos/evermemos-python#accessing-raw-response-data-eg-headers
        """
        return AsyncV1ResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncV1ResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/evermemos/evermemos-python#with_streaming_response
        """
        return AsyncV1ResourceWithStreamingResponse(self)


class V1ResourceWithRawResponse:
    def __init__(self, v1: V1Resource) -> None:
        self._v1 = v1

    @cached_property
    def memories(self) -> MemoriesResourceWithRawResponse:
        return MemoriesResourceWithRawResponse(self._v1.memories)

    @cached_property
    def status(self) -> StatusResourceWithRawResponse:
        return StatusResourceWithRawResponse(self._v1.status)


class AsyncV1ResourceWithRawResponse:
    def __init__(self, v1: AsyncV1Resource) -> None:
        self._v1 = v1

    @cached_property
    def memories(self) -> AsyncMemoriesResourceWithRawResponse:
        return AsyncMemoriesResourceWithRawResponse(self._v1.memories)

    @cached_property
    def status(self) -> AsyncStatusResourceWithRawResponse:
        return AsyncStatusResourceWithRawResponse(self._v1.status)


class V1ResourceWithStreamingResponse:
    def __init__(self, v1: V1Resource) -> None:
        self._v1 = v1

    @cached_property
    def memories(self) -> MemoriesResourceWithStreamingResponse:
        return MemoriesResourceWithStreamingResponse(self._v1.memories)

    @cached_property
    def status(self) -> StatusResourceWithStreamingResponse:
        return StatusResourceWithStreamingResponse(self._v1.status)


class AsyncV1ResourceWithStreamingResponse:
    def __init__(self, v1: AsyncV1Resource) -> None:
        self._v1 = v1

    @cached_property
    def memories(self) -> AsyncMemoriesResourceWithStreamingResponse:
        return AsyncMemoriesResourceWithStreamingResponse(self._v1.memories)

    @cached_property
    def status(self) -> AsyncStatusResourceWithStreamingResponse:
        return AsyncStatusResourceWithStreamingResponse(self._v1.status)

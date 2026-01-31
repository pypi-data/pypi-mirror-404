# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from evermemos import EverMemOS, AsyncEverMemOS
from tests.utils import assert_matches_type
from evermemos.types.v1.status import RequestGetResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRequest:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get(self, client: EverMemOS) -> None:
        request = client.v1.status.request.get(
            request_id="request_id",
        )
        assert_matches_type(RequestGetResponse, request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get(self, client: EverMemOS) -> None:
        response = client.v1.status.request.with_raw_response.get(
            request_id="request_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        request = response.parse()
        assert_matches_type(RequestGetResponse, request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get(self, client: EverMemOS) -> None:
        with client.v1.status.request.with_streaming_response.get(
            request_id="request_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            request = response.parse()
            assert_matches_type(RequestGetResponse, request, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncRequest:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get(self, async_client: AsyncEverMemOS) -> None:
        request = await async_client.v1.status.request.get(
            request_id="request_id",
        )
        assert_matches_type(RequestGetResponse, request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get(self, async_client: AsyncEverMemOS) -> None:
        response = await async_client.v1.status.request.with_raw_response.get(
            request_id="request_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        request = await response.parse()
        assert_matches_type(RequestGetResponse, request, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get(self, async_client: AsyncEverMemOS) -> None:
        async with async_client.v1.status.request.with_streaming_response.get(
            request_id="request_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            request = await response.parse()
            assert_matches_type(RequestGetResponse, request, path=["response"])

        assert cast(Any, response.is_closed) is True

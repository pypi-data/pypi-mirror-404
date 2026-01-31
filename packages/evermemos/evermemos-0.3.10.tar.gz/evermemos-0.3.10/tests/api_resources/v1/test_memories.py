# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from evermemos import EverMemOS, AsyncEverMemOS
from tests.utils import assert_matches_type
from evermemos.types.v1 import (
    MemoryAddResponse,
    MemoryGetResponse,
    MemoryDeleteResponse,
    MemorySearchResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestMemories:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: EverMemOS) -> None:
        memory = client.v1.memories.delete()
        assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete_with_all_params(self, client: EverMemOS) -> None:
        memory = client.v1.memories.delete(
            id="507f1f77bcf86cd799439011",
            event_id="507f1f77bcf86cd799439011",
            group_id="group_456",
            memory_id="507f1f77bcf86cd799439011",
            user_id="user_123",
        )
        assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: EverMemOS) -> None:
        response = client.v1.memories.with_raw_response.delete()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: EverMemOS) -> None:
        with client.v1.memories.with_streaming_response.delete() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_add(self, client: EverMemOS) -> None:
        memory = client.v1.memories.add(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
        )
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_add_with_all_params(self, client: EverMemOS) -> None:
        memory = client.v1.memories.add(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
            flush=False,
            group_id="group_123",
            group_name="Project Discussion Group",
            refer_list=["msg_000"],
            role="user",
            sender_name="John",
        )
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_add(self, client: EverMemOS) -> None:
        response = client.v1.memories.with_raw_response.add(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_add(self, client: EverMemOS) -> None:
        with client.v1.memories.with_streaming_response.add(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemoryAddResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get(self, client: EverMemOS) -> None:
        memory = client.v1.memories.get()
        assert_matches_type(MemoryGetResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get(self, client: EverMemOS) -> None:
        response = client.v1.memories.with_raw_response.get()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemoryGetResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get(self, client: EverMemOS) -> None:
        with client.v1.memories.with_streaming_response.get() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemoryGetResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search(self, client: EverMemOS) -> None:
        memory = client.v1.memories.search()
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_search(self, client: EverMemOS) -> None:
        response = client.v1.memories.with_raw_response.search()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_search(self, client: EverMemOS) -> None:
        with client.v1.memories.with_streaming_response.search() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemorySearchResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncMemories:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncEverMemOS) -> None:
        memory = await async_client.v1.memories.delete()
        assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete_with_all_params(self, async_client: AsyncEverMemOS) -> None:
        memory = await async_client.v1.memories.delete(
            id="507f1f77bcf86cd799439011",
            event_id="507f1f77bcf86cd799439011",
            group_id="group_456",
            memory_id="507f1f77bcf86cd799439011",
            user_id="user_123",
        )
        assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncEverMemOS) -> None:
        response = await async_client.v1.memories.with_raw_response.delete()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncEverMemOS) -> None:
        async with async_client.v1.memories.with_streaming_response.delete() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_add(self, async_client: AsyncEverMemOS) -> None:
        memory = await async_client.v1.memories.add(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
        )
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_add_with_all_params(self, async_client: AsyncEverMemOS) -> None:
        memory = await async_client.v1.memories.add(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
            flush=False,
            group_id="group_123",
            group_name="Project Discussion Group",
            refer_list=["msg_000"],
            role="user",
            sender_name="John",
        )
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_add(self, async_client: AsyncEverMemOS) -> None:
        response = await async_client.v1.memories.with_raw_response.add(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_add(self, async_client: AsyncEverMemOS) -> None:
        async with async_client.v1.memories.with_streaming_response.add(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemoryAddResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get(self, async_client: AsyncEverMemOS) -> None:
        memory = await async_client.v1.memories.get()
        assert_matches_type(MemoryGetResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get(self, async_client: AsyncEverMemOS) -> None:
        response = await async_client.v1.memories.with_raw_response.get()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemoryGetResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get(self, async_client: AsyncEverMemOS) -> None:
        async with async_client.v1.memories.with_streaming_response.get() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemoryGetResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search(self, async_client: AsyncEverMemOS) -> None:
        memory = await async_client.v1.memories.search()
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_search(self, async_client: AsyncEverMemOS) -> None:
        response = await async_client.v1.memories.with_raw_response.search()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_search(self, async_client: AsyncEverMemOS) -> None:
        async with async_client.v1.memories.with_streaming_response.search() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemorySearchResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

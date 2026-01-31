# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from evermemos import EverMemOS, AsyncEverMemOS
from tests.utils import assert_matches_type
from evermemos.types.v1.memories import (
    ConversationMetaGetResponse,
    ConversationMetaCreateResponse,
    ConversationMetaUpdateResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestConversationMeta:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: EverMemOS) -> None:
        conversation_meta = client.v1.memories.conversation_meta.create(
            created_at="2025-01-15T10:00:00+00:00",
        )
        assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: EverMemOS) -> None:
        conversation_meta = client.v1.memories.conversation_meta.create(
            created_at="2025-01-15T10:00:00+00:00",
            default_timezone="UTC",
            description="Technical discussion for new feature development",
            group_id="group_123",
            llm_custom_setting={
                "boundary": {
                    "model": "gpt-4o-mini",
                    "provider": "openai",
                    "extra": {
                        "max_tokens": "bar",
                        "temperature": "bar",
                    },
                },
                "extra": {"foo": "bar"},
                "extraction": {
                    "model": "gpt-4o",
                    "provider": "openai",
                    "extra": {
                        "max_tokens": "bar",
                        "temperature": "bar",
                    },
                },
            },
            name="Project Discussion Group",
            scene="group_chat",
            scene_desc={
                "description": "bar",
                "type": "bar",
            },
            tags=["work", "technical"],
            user_details={
                "bot_001": {
                    "custom_role": "assistant",
                    "extra": {"type": "bar"},
                    "full_name": "AI Assistant",
                    "role": "assistant",
                },
                "user_001": {
                    "custom_role": "developer",
                    "extra": {"department": "bar"},
                    "full_name": "John Smith",
                    "role": "user",
                },
            },
        )
        assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: EverMemOS) -> None:
        response = client.v1.memories.conversation_meta.with_raw_response.create(
            created_at="2025-01-15T10:00:00+00:00",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation_meta = response.parse()
        assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: EverMemOS) -> None:
        with client.v1.memories.conversation_meta.with_streaming_response.create(
            created_at="2025-01-15T10:00:00+00:00",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation_meta = response.parse()
            assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: EverMemOS) -> None:
        conversation_meta = client.v1.memories.conversation_meta.update()
        assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: EverMemOS) -> None:
        conversation_meta = client.v1.memories.conversation_meta.update(
            default_timezone="Asia/Shanghai",
            description="Updated description",
            group_id="group_123",
            llm_custom_setting={
                "boundary": {
                    "model": "gpt-4o-mini",
                    "provider": "openai",
                    "extra": {
                        "max_tokens": "bar",
                        "temperature": "bar",
                    },
                },
                "extra": {"foo": "bar"},
                "extraction": {
                    "model": "gpt-4o",
                    "provider": "openai",
                    "extra": {
                        "max_tokens": "bar",
                        "temperature": "bar",
                    },
                },
            },
            name="New Group Name",
            scene_desc={"description": "bar"},
            tags=["tag1", "tag2"],
            user_details={
                "user_001": {
                    "custom_role": "lead",
                    "extra": {"department": "bar"},
                    "full_name": "John Smith",
                    "role": "user",
                }
            },
        )
        assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: EverMemOS) -> None:
        response = client.v1.memories.conversation_meta.with_raw_response.update()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation_meta = response.parse()
        assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: EverMemOS) -> None:
        with client.v1.memories.conversation_meta.with_streaming_response.update() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation_meta = response.parse()
            assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get(self, client: EverMemOS) -> None:
        conversation_meta = client.v1.memories.conversation_meta.get()
        assert_matches_type(ConversationMetaGetResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get(self, client: EverMemOS) -> None:
        response = client.v1.memories.conversation_meta.with_raw_response.get()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation_meta = response.parse()
        assert_matches_type(ConversationMetaGetResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get(self, client: EverMemOS) -> None:
        with client.v1.memories.conversation_meta.with_streaming_response.get() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation_meta = response.parse()
            assert_matches_type(ConversationMetaGetResponse, conversation_meta, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncConversationMeta:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncEverMemOS) -> None:
        conversation_meta = await async_client.v1.memories.conversation_meta.create(
            created_at="2025-01-15T10:00:00+00:00",
        )
        assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncEverMemOS) -> None:
        conversation_meta = await async_client.v1.memories.conversation_meta.create(
            created_at="2025-01-15T10:00:00+00:00",
            default_timezone="UTC",
            description="Technical discussion for new feature development",
            group_id="group_123",
            llm_custom_setting={
                "boundary": {
                    "model": "gpt-4o-mini",
                    "provider": "openai",
                    "extra": {
                        "max_tokens": "bar",
                        "temperature": "bar",
                    },
                },
                "extra": {"foo": "bar"},
                "extraction": {
                    "model": "gpt-4o",
                    "provider": "openai",
                    "extra": {
                        "max_tokens": "bar",
                        "temperature": "bar",
                    },
                },
            },
            name="Project Discussion Group",
            scene="group_chat",
            scene_desc={
                "description": "bar",
                "type": "bar",
            },
            tags=["work", "technical"],
            user_details={
                "bot_001": {
                    "custom_role": "assistant",
                    "extra": {"type": "bar"},
                    "full_name": "AI Assistant",
                    "role": "assistant",
                },
                "user_001": {
                    "custom_role": "developer",
                    "extra": {"department": "bar"},
                    "full_name": "John Smith",
                    "role": "user",
                },
            },
        )
        assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncEverMemOS) -> None:
        response = await async_client.v1.memories.conversation_meta.with_raw_response.create(
            created_at="2025-01-15T10:00:00+00:00",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation_meta = await response.parse()
        assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncEverMemOS) -> None:
        async with async_client.v1.memories.conversation_meta.with_streaming_response.create(
            created_at="2025-01-15T10:00:00+00:00",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation_meta = await response.parse()
            assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncEverMemOS) -> None:
        conversation_meta = await async_client.v1.memories.conversation_meta.update()
        assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncEverMemOS) -> None:
        conversation_meta = await async_client.v1.memories.conversation_meta.update(
            default_timezone="Asia/Shanghai",
            description="Updated description",
            group_id="group_123",
            llm_custom_setting={
                "boundary": {
                    "model": "gpt-4o-mini",
                    "provider": "openai",
                    "extra": {
                        "max_tokens": "bar",
                        "temperature": "bar",
                    },
                },
                "extra": {"foo": "bar"},
                "extraction": {
                    "model": "gpt-4o",
                    "provider": "openai",
                    "extra": {
                        "max_tokens": "bar",
                        "temperature": "bar",
                    },
                },
            },
            name="New Group Name",
            scene_desc={"description": "bar"},
            tags=["tag1", "tag2"],
            user_details={
                "user_001": {
                    "custom_role": "lead",
                    "extra": {"department": "bar"},
                    "full_name": "John Smith",
                    "role": "user",
                }
            },
        )
        assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncEverMemOS) -> None:
        response = await async_client.v1.memories.conversation_meta.with_raw_response.update()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation_meta = await response.parse()
        assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncEverMemOS) -> None:
        async with async_client.v1.memories.conversation_meta.with_streaming_response.update() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation_meta = await response.parse()
            assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get(self, async_client: AsyncEverMemOS) -> None:
        conversation_meta = await async_client.v1.memories.conversation_meta.get()
        assert_matches_type(ConversationMetaGetResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get(self, async_client: AsyncEverMemOS) -> None:
        response = await async_client.v1.memories.conversation_meta.with_raw_response.get()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation_meta = await response.parse()
        assert_matches_type(ConversationMetaGetResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get(self, async_client: AsyncEverMemOS) -> None:
        async with async_client.v1.memories.conversation_meta.with_streaming_response.get() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation_meta = await response.parse()
            assert_matches_type(ConversationMetaGetResponse, conversation_meta, path=["response"])

        assert cast(Any, response.is_closed) is True

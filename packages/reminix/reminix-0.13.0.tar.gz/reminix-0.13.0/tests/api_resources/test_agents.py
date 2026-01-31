# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from reminix import Reminix, AsyncReminix
from tests.utils import assert_matches_type
from reminix.types import (
    Agent,
    AgentChatResponse,
    AgentInvokeResponse,
)
from reminix.pagination import SyncCursor, AsyncCursor

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAgents:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Reminix) -> None:
        agent = client.agents.retrieve(
            "x",
        )
        assert_matches_type(Agent, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Reminix) -> None:
        response = client.agents.with_raw_response.retrieve(
            "x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        agent = response.parse()
        assert_matches_type(Agent, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Reminix) -> None:
        with client.agents.with_streaming_response.retrieve(
            "x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            agent = response.parse()
            assert_matches_type(Agent, agent, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Reminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `name` but received ''"):
            client.agents.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Reminix) -> None:
        agent = client.agents.list()
        assert_matches_type(SyncCursor[Agent], agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Reminix) -> None:
        agent = client.agents.list(
            cursor="cursor",
            limit=1,
            status="active",
            type="type",
        )
        assert_matches_type(SyncCursor[Agent], agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Reminix) -> None:
        response = client.agents.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        agent = response.parse()
        assert_matches_type(SyncCursor[Agent], agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Reminix) -> None:
        with client.agents.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            agent = response.parse()
            assert_matches_type(SyncCursor[Agent], agent, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_chat_overload_1(self, client: Reminix) -> None:
        agent = client.agents.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                }
            ],
        )
        assert_matches_type(AgentChatResponse, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_chat_with_all_params_overload_1(self, client: Reminix) -> None:
        agent = client.agents.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                    "name": "name",
                    "tool_call_id": "tool_call_id",
                    "tool_calls": [
                        {
                            "id": "id",
                            "function": {
                                "arguments": "arguments",
                                "name": "name",
                            },
                            "type": "function",
                        }
                    ],
                }
            ],
            context={"identity": {"foo": "bar"}},
            conversation_id="conversation_id",
            stream=False,
        )
        assert_matches_type(AgentChatResponse, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_chat_overload_1(self, client: Reminix) -> None:
        response = client.agents.with_raw_response.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        agent = response.parse()
        assert_matches_type(AgentChatResponse, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_chat_overload_1(self, client: Reminix) -> None:
        with client.agents.with_streaming_response.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            agent = response.parse()
            assert_matches_type(AgentChatResponse, agent, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_chat_overload_1(self, client: Reminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `name` but received ''"):
            client.agents.with_raw_response.chat(
                name="",
                messages=[
                    {
                        "content": "string",
                        "role": "system",
                    }
                ],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_chat_overload_2(self, client: Reminix) -> None:
        agent_stream = client.agents.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                }
            ],
            stream=True,
        )
        agent_stream.response.close()

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_chat_with_all_params_overload_2(self, client: Reminix) -> None:
        agent_stream = client.agents.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                    "name": "name",
                    "tool_call_id": "tool_call_id",
                    "tool_calls": [
                        {
                            "id": "id",
                            "function": {
                                "arguments": "arguments",
                                "name": "name",
                            },
                            "type": "function",
                        }
                    ],
                }
            ],
            stream=True,
            context={"identity": {"foo": "bar"}},
            conversation_id="conversation_id",
        )
        agent_stream.response.close()

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_chat_overload_2(self, client: Reminix) -> None:
        response = client.agents.with_raw_response.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                }
            ],
            stream=True,
        )

        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stream = response.parse()
        stream.close()

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_chat_overload_2(self, client: Reminix) -> None:
        with client.agents.with_streaming_response.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                }
            ],
            stream=True,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stream = response.parse()
            stream.close()

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_chat_overload_2(self, client: Reminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `name` but received ''"):
            client.agents.with_raw_response.chat(
                name="",
                messages=[
                    {
                        "content": "string",
                        "role": "system",
                    }
                ],
                stream=True,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_invoke_overload_1(self, client: Reminix) -> None:
        agent = client.agents.invoke(
            name="name",
        )
        assert_matches_type(AgentInvokeResponse, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_invoke_with_all_params_overload_1(self, client: Reminix) -> None:
        agent = client.agents.invoke(
            name="name",
            context={"identity": {"foo": "bar"}},
            stream=False,
        )
        assert_matches_type(AgentInvokeResponse, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_invoke_overload_1(self, client: Reminix) -> None:
        response = client.agents.with_raw_response.invoke(
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        agent = response.parse()
        assert_matches_type(AgentInvokeResponse, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_invoke_overload_1(self, client: Reminix) -> None:
        with client.agents.with_streaming_response.invoke(
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            agent = response.parse()
            assert_matches_type(AgentInvokeResponse, agent, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_invoke_overload_1(self, client: Reminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `name` but received ''"):
            client.agents.with_raw_response.invoke(
                name="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_invoke_overload_2(self, client: Reminix) -> None:
        agent_stream = client.agents.invoke(
            name="name",
            stream=True,
        )
        agent_stream.response.close()

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_invoke_with_all_params_overload_2(self, client: Reminix) -> None:
        agent_stream = client.agents.invoke(
            name="name",
            stream=True,
            context={"identity": {"foo": "bar"}},
        )
        agent_stream.response.close()

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_invoke_overload_2(self, client: Reminix) -> None:
        response = client.agents.with_raw_response.invoke(
            name="name",
            stream=True,
        )

        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stream = response.parse()
        stream.close()

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_invoke_overload_2(self, client: Reminix) -> None:
        with client.agents.with_streaming_response.invoke(
            name="name",
            stream=True,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stream = response.parse()
            stream.close()

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_invoke_overload_2(self, client: Reminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `name` but received ''"):
            client.agents.with_raw_response.invoke(
                name="",
                stream=True,
            )


class TestAsyncAgents:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncReminix) -> None:
        agent = await async_client.agents.retrieve(
            "x",
        )
        assert_matches_type(Agent, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncReminix) -> None:
        response = await async_client.agents.with_raw_response.retrieve(
            "x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        agent = await response.parse()
        assert_matches_type(Agent, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncReminix) -> None:
        async with async_client.agents.with_streaming_response.retrieve(
            "x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            agent = await response.parse()
            assert_matches_type(Agent, agent, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncReminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `name` but received ''"):
            await async_client.agents.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncReminix) -> None:
        agent = await async_client.agents.list()
        assert_matches_type(AsyncCursor[Agent], agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncReminix) -> None:
        agent = await async_client.agents.list(
            cursor="cursor",
            limit=1,
            status="active",
            type="type",
        )
        assert_matches_type(AsyncCursor[Agent], agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncReminix) -> None:
        response = await async_client.agents.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        agent = await response.parse()
        assert_matches_type(AsyncCursor[Agent], agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncReminix) -> None:
        async with async_client.agents.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            agent = await response.parse()
            assert_matches_type(AsyncCursor[Agent], agent, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_chat_overload_1(self, async_client: AsyncReminix) -> None:
        agent = await async_client.agents.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                }
            ],
        )
        assert_matches_type(AgentChatResponse, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_chat_with_all_params_overload_1(self, async_client: AsyncReminix) -> None:
        agent = await async_client.agents.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                    "name": "name",
                    "tool_call_id": "tool_call_id",
                    "tool_calls": [
                        {
                            "id": "id",
                            "function": {
                                "arguments": "arguments",
                                "name": "name",
                            },
                            "type": "function",
                        }
                    ],
                }
            ],
            context={"identity": {"foo": "bar"}},
            conversation_id="conversation_id",
            stream=False,
        )
        assert_matches_type(AgentChatResponse, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_chat_overload_1(self, async_client: AsyncReminix) -> None:
        response = await async_client.agents.with_raw_response.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        agent = await response.parse()
        assert_matches_type(AgentChatResponse, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_chat_overload_1(self, async_client: AsyncReminix) -> None:
        async with async_client.agents.with_streaming_response.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            agent = await response.parse()
            assert_matches_type(AgentChatResponse, agent, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_chat_overload_1(self, async_client: AsyncReminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `name` but received ''"):
            await async_client.agents.with_raw_response.chat(
                name="",
                messages=[
                    {
                        "content": "string",
                        "role": "system",
                    }
                ],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_chat_overload_2(self, async_client: AsyncReminix) -> None:
        agent_stream = await async_client.agents.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                }
            ],
            stream=True,
        )
        await agent_stream.response.aclose()

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_chat_with_all_params_overload_2(self, async_client: AsyncReminix) -> None:
        agent_stream = await async_client.agents.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                    "name": "name",
                    "tool_call_id": "tool_call_id",
                    "tool_calls": [
                        {
                            "id": "id",
                            "function": {
                                "arguments": "arguments",
                                "name": "name",
                            },
                            "type": "function",
                        }
                    ],
                }
            ],
            stream=True,
            context={"identity": {"foo": "bar"}},
            conversation_id="conversation_id",
        )
        await agent_stream.response.aclose()

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_chat_overload_2(self, async_client: AsyncReminix) -> None:
        response = await async_client.agents.with_raw_response.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                }
            ],
            stream=True,
        )

        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stream = await response.parse()
        await stream.close()

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_chat_overload_2(self, async_client: AsyncReminix) -> None:
        async with async_client.agents.with_streaming_response.chat(
            name="name",
            messages=[
                {
                    "content": "string",
                    "role": "system",
                }
            ],
            stream=True,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stream = await response.parse()
            await stream.close()

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_chat_overload_2(self, async_client: AsyncReminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `name` but received ''"):
            await async_client.agents.with_raw_response.chat(
                name="",
                messages=[
                    {
                        "content": "string",
                        "role": "system",
                    }
                ],
                stream=True,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_invoke_overload_1(self, async_client: AsyncReminix) -> None:
        agent = await async_client.agents.invoke(
            name="name",
        )
        assert_matches_type(AgentInvokeResponse, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_invoke_with_all_params_overload_1(self, async_client: AsyncReminix) -> None:
        agent = await async_client.agents.invoke(
            name="name",
            context={"identity": {"foo": "bar"}},
            stream=False,
        )
        assert_matches_type(AgentInvokeResponse, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_invoke_overload_1(self, async_client: AsyncReminix) -> None:
        response = await async_client.agents.with_raw_response.invoke(
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        agent = await response.parse()
        assert_matches_type(AgentInvokeResponse, agent, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_invoke_overload_1(self, async_client: AsyncReminix) -> None:
        async with async_client.agents.with_streaming_response.invoke(
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            agent = await response.parse()
            assert_matches_type(AgentInvokeResponse, agent, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_invoke_overload_1(self, async_client: AsyncReminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `name` but received ''"):
            await async_client.agents.with_raw_response.invoke(
                name="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_invoke_overload_2(self, async_client: AsyncReminix) -> None:
        agent_stream = await async_client.agents.invoke(
            name="name",
            stream=True,
        )
        await agent_stream.response.aclose()

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_invoke_with_all_params_overload_2(self, async_client: AsyncReminix) -> None:
        agent_stream = await async_client.agents.invoke(
            name="name",
            stream=True,
            context={"identity": {"foo": "bar"}},
        )
        await agent_stream.response.aclose()

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_invoke_overload_2(self, async_client: AsyncReminix) -> None:
        response = await async_client.agents.with_raw_response.invoke(
            name="name",
            stream=True,
        )

        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stream = await response.parse()
        await stream.close()

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_invoke_overload_2(self, async_client: AsyncReminix) -> None:
        async with async_client.agents.with_streaming_response.invoke(
            name="name",
            stream=True,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stream = await response.parse()
            await stream.close()

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_invoke_overload_2(self, async_client: AsyncReminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `name` but received ''"):
            await async_client.agents.with_raw_response.invoke(
                name="",
                stream=True,
            )

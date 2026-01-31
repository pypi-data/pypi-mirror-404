# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal, overload

import httpx

from ..types import agent_chat_params, agent_list_params, agent_invoke_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import required_args, maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._streaming import Stream, AsyncStream
from ..pagination import SyncCursor, AsyncCursor
from ..types.agent import Agent
from .._base_client import AsyncPaginator, make_request_options
from ..types.stream_chunk import StreamChunk
from ..types.chat_message_param import ChatMessageParam
from ..types.agent_chat_response import AgentChatResponse
from ..types.agent_invoke_response import AgentInvokeResponse

__all__ = ["AgentsResource", "AsyncAgentsResource"]


class AgentsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AgentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/reminix-ai/reminix-python#accessing-raw-response-data-eg-headers
        """
        return AgentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AgentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/reminix-ai/reminix-python#with_streaming_response
        """
        return AgentsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        name: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Agent:
        """
        Get details of a specific agent by name.

        Args:
          name: Agent name

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not name:
            raise ValueError(f"Expected a non-empty value for `name` but received {name!r}")
        return self._get(
            f"/agents/{name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Agent,
        )

    def list(
        self,
        *,
        cursor: str | Omit = omit,
        limit: float | Omit = omit,
        status: Literal["active", "inactive"] | Omit = omit,
        type: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[Agent]:
        """
        List all agents in the project with optional filtering by type and status.

        Args:
          cursor: Cursor for pagination

          limit: Number of agents to return

          status: Filter by agent status

          type: Filter by agent type (managed, python, typescript, python-langchain, etc.)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/agents",
            page=SyncCursor[Agent],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "cursor": cursor,
                        "limit": limit,
                        "status": status,
                        "type": type,
                    },
                    agent_list_params.AgentListParams,
                ),
            ),
            model=Agent,
        )

    @overload
    def chat(
        self,
        name: str,
        *,
        messages: Iterable[ChatMessageParam],
        context: agent_chat_params.Context | Omit = omit,
        conversation_id: str | Omit = omit,
        stream: Literal[False] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AgentChatResponse:
        """
        Send a chat message to an agent and receive a response.

        **Supported Agents:** Managed agents only. Custom agents should use the /invoke
        endpoint.

        **Tool Calls:** Messages support the OpenAI tool calling format:

        - Assistant messages can include `tool_calls` array with function calls
        - Tool result messages use `role: "tool"` with `tool_call_id` and `name`
        - Content can be `null` when `tool_calls` is present

        **Streaming:** Set `stream: true` to receive Server-Sent Events (SSE) for
        real-time responses.

        Args:
          name: Unique, URL-safe agent name within the project

          messages: Array of chat messages

          context: Optional context for the agent execution

          conversation_id: Conversation ID to continue an existing conversation

          stream: Enable streaming response

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    def chat(
        self,
        name: str,
        *,
        messages: Iterable[ChatMessageParam],
        stream: Literal[True],
        context: agent_chat_params.Context | Omit = omit,
        conversation_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Stream[StreamChunk]:
        """
        Send a chat message to an agent and receive a response.

        **Supported Agents:** Managed agents only. Custom agents should use the /invoke
        endpoint.

        **Tool Calls:** Messages support the OpenAI tool calling format:

        - Assistant messages can include `tool_calls` array with function calls
        - Tool result messages use `role: "tool"` with `tool_call_id` and `name`
        - Content can be `null` when `tool_calls` is present

        **Streaming:** Set `stream: true` to receive Server-Sent Events (SSE) for
        real-time responses.

        Args:
          name: Unique, URL-safe agent name within the project

          messages: Array of chat messages

          stream: Enable streaming response

          context: Optional context for the agent execution

          conversation_id: Conversation ID to continue an existing conversation

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    def chat(
        self,
        name: str,
        *,
        messages: Iterable[ChatMessageParam],
        stream: bool,
        context: agent_chat_params.Context | Omit = omit,
        conversation_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AgentChatResponse | Stream[StreamChunk]:
        """
        Send a chat message to an agent and receive a response.

        **Supported Agents:** Managed agents only. Custom agents should use the /invoke
        endpoint.

        **Tool Calls:** Messages support the OpenAI tool calling format:

        - Assistant messages can include `tool_calls` array with function calls
        - Tool result messages use `role: "tool"` with `tool_call_id` and `name`
        - Content can be `null` when `tool_calls` is present

        **Streaming:** Set `stream: true` to receive Server-Sent Events (SSE) for
        real-time responses.

        Args:
          name: Unique, URL-safe agent name within the project

          messages: Array of chat messages

          stream: Enable streaming response

          context: Optional context for the agent execution

          conversation_id: Conversation ID to continue an existing conversation

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @required_args(["messages"], ["messages", "stream"])
    def chat(
        self,
        name: str,
        *,
        messages: Iterable[ChatMessageParam],
        context: agent_chat_params.Context | Omit = omit,
        conversation_id: str | Omit = omit,
        stream: Literal[False] | Literal[True] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AgentChatResponse | Stream[StreamChunk]:
        if not name:
            raise ValueError(f"Expected a non-empty value for `name` but received {name!r}")
        return self._post(
            f"/agents/{name}/chat",
            body=maybe_transform(
                {
                    "messages": messages,
                    "context": context,
                    "conversation_id": conversation_id,
                    "stream": stream,
                },
                agent_chat_params.AgentChatParamsStreaming if stream else agent_chat_params.AgentChatParamsNonStreaming,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AgentChatResponse,
            stream=stream or False,
            stream_cls=Stream[StreamChunk],
        )

    @overload
    def invoke(
        self,
        name: str,
        *,
        context: agent_invoke_params.Context | Omit = omit,
        stream: Literal[False] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AgentInvokeResponse:
        """
        Invoke a custom agent with the provided input.

        **Supported Agents:** Custom agents only. Managed agents should use the /chat
        endpoint.

        **Input:** Pass structured input data matching the agent's parameter schema.

        **Timeout:** Agent invocations have a 60-second timeout. If the agent takes
        longer to respond, you will receive a 504 Gateway Timeout error. For
        long-running tasks, consider using streaming mode which does not have the same
        timeout constraints.

        **Idempotency:** For non-streaming requests, send an `Idempotency-Key` header
        with a unique value (e.g., UUID) to ensure duplicate requests return the same
        response. Keys are valid for 24 hours. Streaming responses are not cached.

        **Streaming:** Set `stream: true` in the request body to receive Server-Sent
        Events (SSE) stream with incremental chunks. Useful for long-running tasks or
        real-time responses.

        Args:
          name: Unique, URL-safe agent name within the project

          context: Optional context for the agent execution

          stream: Enable streaming response (SSE)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    def invoke(
        self,
        name: str,
        *,
        stream: Literal[True],
        context: agent_invoke_params.Context | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Stream[StreamChunk]:
        """
        Invoke a custom agent with the provided input.

        **Supported Agents:** Custom agents only. Managed agents should use the /chat
        endpoint.

        **Input:** Pass structured input data matching the agent's parameter schema.

        **Timeout:** Agent invocations have a 60-second timeout. If the agent takes
        longer to respond, you will receive a 504 Gateway Timeout error. For
        long-running tasks, consider using streaming mode which does not have the same
        timeout constraints.

        **Idempotency:** For non-streaming requests, send an `Idempotency-Key` header
        with a unique value (e.g., UUID) to ensure duplicate requests return the same
        response. Keys are valid for 24 hours. Streaming responses are not cached.

        **Streaming:** Set `stream: true` in the request body to receive Server-Sent
        Events (SSE) stream with incremental chunks. Useful for long-running tasks or
        real-time responses.

        Args:
          name: Unique, URL-safe agent name within the project

          stream: Enable streaming response (SSE)

          context: Optional context for the agent execution

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    def invoke(
        self,
        name: str,
        *,
        stream: bool,
        context: agent_invoke_params.Context | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AgentInvokeResponse | Stream[StreamChunk]:
        """
        Invoke a custom agent with the provided input.

        **Supported Agents:** Custom agents only. Managed agents should use the /chat
        endpoint.

        **Input:** Pass structured input data matching the agent's parameter schema.

        **Timeout:** Agent invocations have a 60-second timeout. If the agent takes
        longer to respond, you will receive a 504 Gateway Timeout error. For
        long-running tasks, consider using streaming mode which does not have the same
        timeout constraints.

        **Idempotency:** For non-streaming requests, send an `Idempotency-Key` header
        with a unique value (e.g., UUID) to ensure duplicate requests return the same
        response. Keys are valid for 24 hours. Streaming responses are not cached.

        **Streaming:** Set `stream: true` in the request body to receive Server-Sent
        Events (SSE) stream with incremental chunks. Useful for long-running tasks or
        real-time responses.

        Args:
          name: Unique, URL-safe agent name within the project

          stream: Enable streaming response (SSE)

          context: Optional context for the agent execution

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    def invoke(
        self,
        name: str,
        *,
        context: agent_invoke_params.Context | Omit = omit,
        stream: Literal[False] | Literal[True] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AgentInvokeResponse | Stream[StreamChunk]:
        if not name:
            raise ValueError(f"Expected a non-empty value for `name` but received {name!r}")
        return self._post(
            f"/agents/{name}/invoke",
            body=maybe_transform(
                {
                    "context": context,
                    "stream": stream,
                },
                agent_invoke_params.AgentInvokeParamsStreaming
                if stream
                else agent_invoke_params.AgentInvokeParamsNonStreaming,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AgentInvokeResponse,
            stream=stream or False,
            stream_cls=Stream[StreamChunk],
        )


class AsyncAgentsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAgentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/reminix-ai/reminix-python#accessing-raw-response-data-eg-headers
        """
        return AsyncAgentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAgentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/reminix-ai/reminix-python#with_streaming_response
        """
        return AsyncAgentsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        name: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Agent:
        """
        Get details of a specific agent by name.

        Args:
          name: Agent name

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not name:
            raise ValueError(f"Expected a non-empty value for `name` but received {name!r}")
        return await self._get(
            f"/agents/{name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Agent,
        )

    def list(
        self,
        *,
        cursor: str | Omit = omit,
        limit: float | Omit = omit,
        status: Literal["active", "inactive"] | Omit = omit,
        type: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[Agent, AsyncCursor[Agent]]:
        """
        List all agents in the project with optional filtering by type and status.

        Args:
          cursor: Cursor for pagination

          limit: Number of agents to return

          status: Filter by agent status

          type: Filter by agent type (managed, python, typescript, python-langchain, etc.)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/agents",
            page=AsyncCursor[Agent],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "cursor": cursor,
                        "limit": limit,
                        "status": status,
                        "type": type,
                    },
                    agent_list_params.AgentListParams,
                ),
            ),
            model=Agent,
        )

    @overload
    async def chat(
        self,
        name: str,
        *,
        messages: Iterable[ChatMessageParam],
        context: agent_chat_params.Context | Omit = omit,
        conversation_id: str | Omit = omit,
        stream: Literal[False] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AgentChatResponse:
        """
        Send a chat message to an agent and receive a response.

        **Supported Agents:** Managed agents only. Custom agents should use the /invoke
        endpoint.

        **Tool Calls:** Messages support the OpenAI tool calling format:

        - Assistant messages can include `tool_calls` array with function calls
        - Tool result messages use `role: "tool"` with `tool_call_id` and `name`
        - Content can be `null` when `tool_calls` is present

        **Streaming:** Set `stream: true` to receive Server-Sent Events (SSE) for
        real-time responses.

        Args:
          name: Unique, URL-safe agent name within the project

          messages: Array of chat messages

          context: Optional context for the agent execution

          conversation_id: Conversation ID to continue an existing conversation

          stream: Enable streaming response

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    async def chat(
        self,
        name: str,
        *,
        messages: Iterable[ChatMessageParam],
        stream: Literal[True],
        context: agent_chat_params.Context | Omit = omit,
        conversation_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncStream[StreamChunk]:
        """
        Send a chat message to an agent and receive a response.

        **Supported Agents:** Managed agents only. Custom agents should use the /invoke
        endpoint.

        **Tool Calls:** Messages support the OpenAI tool calling format:

        - Assistant messages can include `tool_calls` array with function calls
        - Tool result messages use `role: "tool"` with `tool_call_id` and `name`
        - Content can be `null` when `tool_calls` is present

        **Streaming:** Set `stream: true` to receive Server-Sent Events (SSE) for
        real-time responses.

        Args:
          name: Unique, URL-safe agent name within the project

          messages: Array of chat messages

          stream: Enable streaming response

          context: Optional context for the agent execution

          conversation_id: Conversation ID to continue an existing conversation

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    async def chat(
        self,
        name: str,
        *,
        messages: Iterable[ChatMessageParam],
        stream: bool,
        context: agent_chat_params.Context | Omit = omit,
        conversation_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AgentChatResponse | AsyncStream[StreamChunk]:
        """
        Send a chat message to an agent and receive a response.

        **Supported Agents:** Managed agents only. Custom agents should use the /invoke
        endpoint.

        **Tool Calls:** Messages support the OpenAI tool calling format:

        - Assistant messages can include `tool_calls` array with function calls
        - Tool result messages use `role: "tool"` with `tool_call_id` and `name`
        - Content can be `null` when `tool_calls` is present

        **Streaming:** Set `stream: true` to receive Server-Sent Events (SSE) for
        real-time responses.

        Args:
          name: Unique, URL-safe agent name within the project

          messages: Array of chat messages

          stream: Enable streaming response

          context: Optional context for the agent execution

          conversation_id: Conversation ID to continue an existing conversation

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @required_args(["messages"], ["messages", "stream"])
    async def chat(
        self,
        name: str,
        *,
        messages: Iterable[ChatMessageParam],
        context: agent_chat_params.Context | Omit = omit,
        conversation_id: str | Omit = omit,
        stream: Literal[False] | Literal[True] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AgentChatResponse | AsyncStream[StreamChunk]:
        if not name:
            raise ValueError(f"Expected a non-empty value for `name` but received {name!r}")
        return await self._post(
            f"/agents/{name}/chat",
            body=await async_maybe_transform(
                {
                    "messages": messages,
                    "context": context,
                    "conversation_id": conversation_id,
                    "stream": stream,
                },
                agent_chat_params.AgentChatParamsStreaming if stream else agent_chat_params.AgentChatParamsNonStreaming,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AgentChatResponse,
            stream=stream or False,
            stream_cls=AsyncStream[StreamChunk],
        )

    @overload
    async def invoke(
        self,
        name: str,
        *,
        context: agent_invoke_params.Context | Omit = omit,
        stream: Literal[False] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AgentInvokeResponse:
        """
        Invoke a custom agent with the provided input.

        **Supported Agents:** Custom agents only. Managed agents should use the /chat
        endpoint.

        **Input:** Pass structured input data matching the agent's parameter schema.

        **Timeout:** Agent invocations have a 60-second timeout. If the agent takes
        longer to respond, you will receive a 504 Gateway Timeout error. For
        long-running tasks, consider using streaming mode which does not have the same
        timeout constraints.

        **Idempotency:** For non-streaming requests, send an `Idempotency-Key` header
        with a unique value (e.g., UUID) to ensure duplicate requests return the same
        response. Keys are valid for 24 hours. Streaming responses are not cached.

        **Streaming:** Set `stream: true` in the request body to receive Server-Sent
        Events (SSE) stream with incremental chunks. Useful for long-running tasks or
        real-time responses.

        Args:
          name: Unique, URL-safe agent name within the project

          context: Optional context for the agent execution

          stream: Enable streaming response (SSE)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    async def invoke(
        self,
        name: str,
        *,
        stream: Literal[True],
        context: agent_invoke_params.Context | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncStream[StreamChunk]:
        """
        Invoke a custom agent with the provided input.

        **Supported Agents:** Custom agents only. Managed agents should use the /chat
        endpoint.

        **Input:** Pass structured input data matching the agent's parameter schema.

        **Timeout:** Agent invocations have a 60-second timeout. If the agent takes
        longer to respond, you will receive a 504 Gateway Timeout error. For
        long-running tasks, consider using streaming mode which does not have the same
        timeout constraints.

        **Idempotency:** For non-streaming requests, send an `Idempotency-Key` header
        with a unique value (e.g., UUID) to ensure duplicate requests return the same
        response. Keys are valid for 24 hours. Streaming responses are not cached.

        **Streaming:** Set `stream: true` in the request body to receive Server-Sent
        Events (SSE) stream with incremental chunks. Useful for long-running tasks or
        real-time responses.

        Args:
          name: Unique, URL-safe agent name within the project

          stream: Enable streaming response (SSE)

          context: Optional context for the agent execution

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    async def invoke(
        self,
        name: str,
        *,
        stream: bool,
        context: agent_invoke_params.Context | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AgentInvokeResponse | AsyncStream[StreamChunk]:
        """
        Invoke a custom agent with the provided input.

        **Supported Agents:** Custom agents only. Managed agents should use the /chat
        endpoint.

        **Input:** Pass structured input data matching the agent's parameter schema.

        **Timeout:** Agent invocations have a 60-second timeout. If the agent takes
        longer to respond, you will receive a 504 Gateway Timeout error. For
        long-running tasks, consider using streaming mode which does not have the same
        timeout constraints.

        **Idempotency:** For non-streaming requests, send an `Idempotency-Key` header
        with a unique value (e.g., UUID) to ensure duplicate requests return the same
        response. Keys are valid for 24 hours. Streaming responses are not cached.

        **Streaming:** Set `stream: true` in the request body to receive Server-Sent
        Events (SSE) stream with incremental chunks. Useful for long-running tasks or
        real-time responses.

        Args:
          name: Unique, URL-safe agent name within the project

          stream: Enable streaming response (SSE)

          context: Optional context for the agent execution

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    async def invoke(
        self,
        name: str,
        *,
        context: agent_invoke_params.Context | Omit = omit,
        stream: Literal[False] | Literal[True] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AgentInvokeResponse | AsyncStream[StreamChunk]:
        if not name:
            raise ValueError(f"Expected a non-empty value for `name` but received {name!r}")
        return await self._post(
            f"/agents/{name}/invoke",
            body=await async_maybe_transform(
                {
                    "context": context,
                    "stream": stream,
                },
                agent_invoke_params.AgentInvokeParamsStreaming
                if stream
                else agent_invoke_params.AgentInvokeParamsNonStreaming,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AgentInvokeResponse,
            stream=stream or False,
            stream_cls=AsyncStream[StreamChunk],
        )


class AgentsResourceWithRawResponse:
    def __init__(self, agents: AgentsResource) -> None:
        self._agents = agents

        self.retrieve = to_raw_response_wrapper(
            agents.retrieve,
        )
        self.list = to_raw_response_wrapper(
            agents.list,
        )
        self.chat = to_raw_response_wrapper(
            agents.chat,
        )
        self.invoke = to_raw_response_wrapper(
            agents.invoke,
        )


class AsyncAgentsResourceWithRawResponse:
    def __init__(self, agents: AsyncAgentsResource) -> None:
        self._agents = agents

        self.retrieve = async_to_raw_response_wrapper(
            agents.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            agents.list,
        )
        self.chat = async_to_raw_response_wrapper(
            agents.chat,
        )
        self.invoke = async_to_raw_response_wrapper(
            agents.invoke,
        )


class AgentsResourceWithStreamingResponse:
    def __init__(self, agents: AgentsResource) -> None:
        self._agents = agents

        self.retrieve = to_streamed_response_wrapper(
            agents.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            agents.list,
        )
        self.chat = to_streamed_response_wrapper(
            agents.chat,
        )
        self.invoke = to_streamed_response_wrapper(
            agents.invoke,
        )


class AsyncAgentsResourceWithStreamingResponse:
    def __init__(self, agents: AsyncAgentsResource) -> None:
        self._agents = agents

        self.retrieve = async_to_streamed_response_wrapper(
            agents.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            agents.list,
        )
        self.chat = async_to_streamed_response_wrapper(
            agents.chat,
        )
        self.invoke = async_to_streamed_response_wrapper(
            agents.invoke,
        )

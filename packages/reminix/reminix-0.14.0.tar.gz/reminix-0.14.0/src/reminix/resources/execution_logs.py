# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..types import execution_log_list_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..pagination import SyncCursor, AsyncCursor
from .._base_client import AsyncPaginator, make_request_options
from ..types.execution_log import ExecutionLog

__all__ = ["ExecutionLogsResource", "AsyncExecutionLogsResource"]


class ExecutionLogsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ExecutionLogsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/reminix-ai/reminix-python#accessing-raw-response-data-eg-headers
        """
        return ExecutionLogsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ExecutionLogsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/reminix-ai/reminix-python#with_streaming_response
        """
        return ExecutionLogsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExecutionLog:
        """
        Get details of a specific execution log by ID.

        Args:
          id: Execution log ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/execution-logs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExecutionLog,
        )

    def list(
        self,
        *,
        cursor: str | Omit = omit,
        limit: float | Omit = omit,
        name: str | Omit = omit,
        source: Literal["api", "cli", "dashboard", "widget", "sdk"] | Omit = omit,
        status: Literal["success", "error", "timeout"] | Omit = omit,
        type: Literal["agent_invoke", "agent_chat", "tool_call"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[ExecutionLog]:
        """
        List execution logs for the project with optional filtering.

        Execution logs track all agent invocations, chats, and tool executions. Use
        filters to narrow down results by type, source, name, or status.

        **Filters:**

        - `type`: Filter by execution type (agent_invoke, agent_chat, tool_call)
        - `source`: Filter by request source (api, cli, dashboard, widget, sdk)
        - `name`: Filter by agent or tool name
        - `status`: Filter by result status (success, error, timeout)

        Args:
          cursor: Cursor for pagination

          limit: Number of logs to return

          name: Filter by agent or tool name

          source: Filter by request source

          status: Filter by execution status

          type: Filter by execution type

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/execution-logs",
            page=SyncCursor[ExecutionLog],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "cursor": cursor,
                        "limit": limit,
                        "name": name,
                        "source": source,
                        "status": status,
                        "type": type,
                    },
                    execution_log_list_params.ExecutionLogListParams,
                ),
            ),
            model=ExecutionLog,
        )


class AsyncExecutionLogsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncExecutionLogsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/reminix-ai/reminix-python#accessing-raw-response-data-eg-headers
        """
        return AsyncExecutionLogsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncExecutionLogsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/reminix-ai/reminix-python#with_streaming_response
        """
        return AsyncExecutionLogsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExecutionLog:
        """
        Get details of a specific execution log by ID.

        Args:
          id: Execution log ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/execution-logs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExecutionLog,
        )

    def list(
        self,
        *,
        cursor: str | Omit = omit,
        limit: float | Omit = omit,
        name: str | Omit = omit,
        source: Literal["api", "cli", "dashboard", "widget", "sdk"] | Omit = omit,
        status: Literal["success", "error", "timeout"] | Omit = omit,
        type: Literal["agent_invoke", "agent_chat", "tool_call"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[ExecutionLog, AsyncCursor[ExecutionLog]]:
        """
        List execution logs for the project with optional filtering.

        Execution logs track all agent invocations, chats, and tool executions. Use
        filters to narrow down results by type, source, name, or status.

        **Filters:**

        - `type`: Filter by execution type (agent_invoke, agent_chat, tool_call)
        - `source`: Filter by request source (api, cli, dashboard, widget, sdk)
        - `name`: Filter by agent or tool name
        - `status`: Filter by result status (success, error, timeout)

        Args:
          cursor: Cursor for pagination

          limit: Number of logs to return

          name: Filter by agent or tool name

          source: Filter by request source

          status: Filter by execution status

          type: Filter by execution type

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/execution-logs",
            page=AsyncCursor[ExecutionLog],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "cursor": cursor,
                        "limit": limit,
                        "name": name,
                        "source": source,
                        "status": status,
                        "type": type,
                    },
                    execution_log_list_params.ExecutionLogListParams,
                ),
            ),
            model=ExecutionLog,
        )


class ExecutionLogsResourceWithRawResponse:
    def __init__(self, execution_logs: ExecutionLogsResource) -> None:
        self._execution_logs = execution_logs

        self.retrieve = to_raw_response_wrapper(
            execution_logs.retrieve,
        )
        self.list = to_raw_response_wrapper(
            execution_logs.list,
        )


class AsyncExecutionLogsResourceWithRawResponse:
    def __init__(self, execution_logs: AsyncExecutionLogsResource) -> None:
        self._execution_logs = execution_logs

        self.retrieve = async_to_raw_response_wrapper(
            execution_logs.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            execution_logs.list,
        )


class ExecutionLogsResourceWithStreamingResponse:
    def __init__(self, execution_logs: ExecutionLogsResource) -> None:
        self._execution_logs = execution_logs

        self.retrieve = to_streamed_response_wrapper(
            execution_logs.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            execution_logs.list,
        )


class AsyncExecutionLogsResourceWithStreamingResponse:
    def __init__(self, execution_logs: AsyncExecutionLogsResource) -> None:
        self._execution_logs = execution_logs

        self.retrieve = async_to_streamed_response_wrapper(
            execution_logs.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            execution_logs.list,
        )

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Literal

import httpx

from ..types import tool_call_params, tool_list_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..pagination import SyncCursor, AsyncCursor
from ..types.tool import Tool
from .._base_client import AsyncPaginator, make_request_options
from ..types.tool_call_response import ToolCallResponse

__all__ = ["ToolsResource", "AsyncToolsResource"]


class ToolsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ToolsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/reminix-ai/reminix-python#accessing-raw-response-data-eg-headers
        """
        return ToolsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ToolsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/reminix-ai/reminix-python#with_streaming_response
        """
        return ToolsResourceWithStreamingResponse(self)

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
    ) -> Tool:
        """
        Get details of a specific tool by name.

        Args:
          name: Tool name

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not name:
            raise ValueError(f"Expected a non-empty value for `name` but received {name!r}")
        return self._get(
            f"/tools/{name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Tool,
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
    ) -> SyncCursor[Tool]:
        """List all tools in the project with optional filtering by type and status.

        Tools
        are automatically discovered from deployments.

        Args:
          cursor: Cursor for pagination

          limit: Number of tools to return

          status: Filter by tool status

          type: Filter by tool type (python, typescript)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/tools",
            page=SyncCursor[Tool],
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
                    tool_list_params.ToolListParams,
                ),
            ),
            model=Tool,
        )

    def call(
        self,
        name: str,
        *,
        input: Dict[str, Optional[object]],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ToolCallResponse:
        """
        Call a tool with the provided input parameters.

        **Timeout:** Tool calls have a 60-second timeout. If the tool takes longer to
        respond, you will receive a 504 Gateway Timeout error.

        **Use cases:**

        - Calling custom tools from your deployment
        - Invoking utility functions
        - Integrating with external services via tools

        Args:
          name: Tool name

          input: Input parameters for the tool. Structure depends on tool definition.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not name:
            raise ValueError(f"Expected a non-empty value for `name` but received {name!r}")
        return self._post(
            f"/tools/{name}/call",
            body=maybe_transform({"input": input}, tool_call_params.ToolCallParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ToolCallResponse,
        )


class AsyncToolsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncToolsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/reminix-ai/reminix-python#accessing-raw-response-data-eg-headers
        """
        return AsyncToolsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncToolsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/reminix-ai/reminix-python#with_streaming_response
        """
        return AsyncToolsResourceWithStreamingResponse(self)

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
    ) -> Tool:
        """
        Get details of a specific tool by name.

        Args:
          name: Tool name

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not name:
            raise ValueError(f"Expected a non-empty value for `name` but received {name!r}")
        return await self._get(
            f"/tools/{name}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Tool,
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
    ) -> AsyncPaginator[Tool, AsyncCursor[Tool]]:
        """List all tools in the project with optional filtering by type and status.

        Tools
        are automatically discovered from deployments.

        Args:
          cursor: Cursor for pagination

          limit: Number of tools to return

          status: Filter by tool status

          type: Filter by tool type (python, typescript)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/tools",
            page=AsyncCursor[Tool],
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
                    tool_list_params.ToolListParams,
                ),
            ),
            model=Tool,
        )

    async def call(
        self,
        name: str,
        *,
        input: Dict[str, Optional[object]],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ToolCallResponse:
        """
        Call a tool with the provided input parameters.

        **Timeout:** Tool calls have a 60-second timeout. If the tool takes longer to
        respond, you will receive a 504 Gateway Timeout error.

        **Use cases:**

        - Calling custom tools from your deployment
        - Invoking utility functions
        - Integrating with external services via tools

        Args:
          name: Tool name

          input: Input parameters for the tool. Structure depends on tool definition.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not name:
            raise ValueError(f"Expected a non-empty value for `name` but received {name!r}")
        return await self._post(
            f"/tools/{name}/call",
            body=await async_maybe_transform({"input": input}, tool_call_params.ToolCallParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ToolCallResponse,
        )


class ToolsResourceWithRawResponse:
    def __init__(self, tools: ToolsResource) -> None:
        self._tools = tools

        self.retrieve = to_raw_response_wrapper(
            tools.retrieve,
        )
        self.list = to_raw_response_wrapper(
            tools.list,
        )
        self.call = to_raw_response_wrapper(
            tools.call,
        )


class AsyncToolsResourceWithRawResponse:
    def __init__(self, tools: AsyncToolsResource) -> None:
        self._tools = tools

        self.retrieve = async_to_raw_response_wrapper(
            tools.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            tools.list,
        )
        self.call = async_to_raw_response_wrapper(
            tools.call,
        )


class ToolsResourceWithStreamingResponse:
    def __init__(self, tools: ToolsResource) -> None:
        self._tools = tools

        self.retrieve = to_streamed_response_wrapper(
            tools.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            tools.list,
        )
        self.call = to_streamed_response_wrapper(
            tools.call,
        )


class AsyncToolsResourceWithStreamingResponse:
    def __init__(self, tools: AsyncToolsResource) -> None:
        self._tools = tools

        self.retrieve = async_to_streamed_response_wrapper(
            tools.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            tools.list,
        )
        self.call = async_to_streamed_response_wrapper(
            tools.call,
        )

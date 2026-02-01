# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Optional
from datetime import datetime

import httpx

from ..types import memory_store_params
from .._types import Body, Omit, Query, Headers, NoneType, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.memory import Memory
from ..types.memory_list_response import MemoryListResponse
from ..types.memory_delete_all_response import MemoryDeleteAllResponse

__all__ = ["MemoryResource", "AsyncMemoryResource"]


class MemoryResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> MemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/reminix-ai/reminix-python#accessing-raw-response-data-eg-headers
        """
        return MemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/reminix-ai/reminix-python#with_streaming_response
        """
        return MemoryResourceWithStreamingResponse(self)

    def retrieve(
        self,
        key: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Memory:
        """
        Get a memory value by key for a specific identity.

        Identity is specified via query parameters with the `identity.` prefix.

        Args:
          key: Memory key

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not key:
            raise ValueError(f"Expected a non-empty value for `key` but received {key!r}")
        return self._get(
            f"/memory/{key}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Memory,
        )

    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryListResponse:
        """
        List all memory keys for a specific identity.

        Identity is specified via query parameters with the `identity.` prefix. For
        example: `?identity.user_id=user_123&identity.tenant_id=acme`

        Returns memory keys and metadata (not full values for efficiency).
        """
        return self._get(
            "/memory",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryListResponse,
        )

    def delete(
        self,
        key: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a memory by key for a specific identity.

        Args:
          key: Memory key

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not key:
            raise ValueError(f"Expected a non-empty value for `key` but received {key!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/memory/{key}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def delete_all(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryDeleteAllResponse:
        """Delete all memories for a specific identity."""
        return self._delete(
            "/memory",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryDeleteAllResponse,
        )

    def store(
        self,
        *,
        identity: Dict[str, Optional[object]],
        key: str,
        expires_at: Union[str, datetime] | Omit = omit,
        value: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Memory:
        """
        Store a key-value memory for a specific identity.

        If a memory with the same key already exists, it will be updated.

        Args:
          identity: Identity fields for memory scoping (e.g., user_id, tenant_id)

          key: Memory key

          expires_at: Optional expiration time (ISO 8601)

          value: Value to store

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/memory",
            body=maybe_transform(
                {
                    "identity": identity,
                    "key": key,
                    "expires_at": expires_at,
                    "value": value,
                },
                memory_store_params.MemoryStoreParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Memory,
        )


class AsyncMemoryResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncMemoryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/reminix-ai/reminix-python#accessing-raw-response-data-eg-headers
        """
        return AsyncMemoryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMemoryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/reminix-ai/reminix-python#with_streaming_response
        """
        return AsyncMemoryResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        key: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Memory:
        """
        Get a memory value by key for a specific identity.

        Identity is specified via query parameters with the `identity.` prefix.

        Args:
          key: Memory key

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not key:
            raise ValueError(f"Expected a non-empty value for `key` but received {key!r}")
        return await self._get(
            f"/memory/{key}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Memory,
        )

    async def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryListResponse:
        """
        List all memory keys for a specific identity.

        Identity is specified via query parameters with the `identity.` prefix. For
        example: `?identity.user_id=user_123&identity.tenant_id=acme`

        Returns memory keys and metadata (not full values for efficiency).
        """
        return await self._get(
            "/memory",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryListResponse,
        )

    async def delete(
        self,
        key: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete a memory by key for a specific identity.

        Args:
          key: Memory key

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not key:
            raise ValueError(f"Expected a non-empty value for `key` but received {key!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/memory/{key}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def delete_all(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryDeleteAllResponse:
        """Delete all memories for a specific identity."""
        return await self._delete(
            "/memory",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryDeleteAllResponse,
        )

    async def store(
        self,
        *,
        identity: Dict[str, Optional[object]],
        key: str,
        expires_at: Union[str, datetime] | Omit = omit,
        value: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Memory:
        """
        Store a key-value memory for a specific identity.

        If a memory with the same key already exists, it will be updated.

        Args:
          identity: Identity fields for memory scoping (e.g., user_id, tenant_id)

          key: Memory key

          expires_at: Optional expiration time (ISO 8601)

          value: Value to store

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/memory",
            body=await async_maybe_transform(
                {
                    "identity": identity,
                    "key": key,
                    "expires_at": expires_at,
                    "value": value,
                },
                memory_store_params.MemoryStoreParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Memory,
        )


class MemoryResourceWithRawResponse:
    def __init__(self, memory: MemoryResource) -> None:
        self._memory = memory

        self.retrieve = to_raw_response_wrapper(
            memory.retrieve,
        )
        self.list = to_raw_response_wrapper(
            memory.list,
        )
        self.delete = to_raw_response_wrapper(
            memory.delete,
        )
        self.delete_all = to_raw_response_wrapper(
            memory.delete_all,
        )
        self.store = to_raw_response_wrapper(
            memory.store,
        )


class AsyncMemoryResourceWithRawResponse:
    def __init__(self, memory: AsyncMemoryResource) -> None:
        self._memory = memory

        self.retrieve = async_to_raw_response_wrapper(
            memory.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            memory.list,
        )
        self.delete = async_to_raw_response_wrapper(
            memory.delete,
        )
        self.delete_all = async_to_raw_response_wrapper(
            memory.delete_all,
        )
        self.store = async_to_raw_response_wrapper(
            memory.store,
        )


class MemoryResourceWithStreamingResponse:
    def __init__(self, memory: MemoryResource) -> None:
        self._memory = memory

        self.retrieve = to_streamed_response_wrapper(
            memory.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            memory.list,
        )
        self.delete = to_streamed_response_wrapper(
            memory.delete,
        )
        self.delete_all = to_streamed_response_wrapper(
            memory.delete_all,
        )
        self.store = to_streamed_response_wrapper(
            memory.store,
        )


class AsyncMemoryResourceWithStreamingResponse:
    def __init__(self, memory: AsyncMemoryResource) -> None:
        self._memory = memory

        self.retrieve = async_to_streamed_response_wrapper(
            memory.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            memory.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            memory.delete,
        )
        self.delete_all = async_to_streamed_response_wrapper(
            memory.delete_all,
        )
        self.store = async_to_streamed_response_wrapper(
            memory.store,
        )

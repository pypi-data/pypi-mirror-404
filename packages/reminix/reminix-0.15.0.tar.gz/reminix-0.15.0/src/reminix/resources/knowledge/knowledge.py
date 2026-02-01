# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...types import knowledge_search_params
from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from .collections.collections import (
    CollectionsResource,
    AsyncCollectionsResource,
    CollectionsResourceWithRawResponse,
    AsyncCollectionsResourceWithRawResponse,
    CollectionsResourceWithStreamingResponse,
    AsyncCollectionsResourceWithStreamingResponse,
)
from ...types.knowledge_search_response import KnowledgeSearchResponse

__all__ = ["KnowledgeResource", "AsyncKnowledgeResource"]


class KnowledgeResource(SyncAPIResource):
    @cached_property
    def collections(self) -> CollectionsResource:
        return CollectionsResource(self._client)

    @cached_property
    def with_raw_response(self) -> KnowledgeResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/reminix-ai/reminix-python#accessing-raw-response-data-eg-headers
        """
        return KnowledgeResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> KnowledgeResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/reminix-ai/reminix-python#with_streaming_response
        """
        return KnowledgeResourceWithStreamingResponse(self)

    def search(
        self,
        *,
        collection_ids: SequenceNotStr[str],
        query: str,
        limit: float | Omit = omit,
        threshold: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KnowledgeSearchResponse:
        """
        Search across one or more knowledge collections using semantic similarity.

        The search uses vector embeddings to find the most relevant content. Results are
        ordered by relevance score (0-1, higher is more similar).

        Args:
          collection_ids: Collection IDs to search

          query: Natural language search query

          limit: Maximum number of results

          threshold: Minimum similarity score (0-1)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/knowledge/search",
            body=maybe_transform(
                {
                    "collection_ids": collection_ids,
                    "query": query,
                    "limit": limit,
                    "threshold": threshold,
                },
                knowledge_search_params.KnowledgeSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=KnowledgeSearchResponse,
        )


class AsyncKnowledgeResource(AsyncAPIResource):
    @cached_property
    def collections(self) -> AsyncCollectionsResource:
        return AsyncCollectionsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncKnowledgeResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/reminix-ai/reminix-python#accessing-raw-response-data-eg-headers
        """
        return AsyncKnowledgeResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncKnowledgeResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/reminix-ai/reminix-python#with_streaming_response
        """
        return AsyncKnowledgeResourceWithStreamingResponse(self)

    async def search(
        self,
        *,
        collection_ids: SequenceNotStr[str],
        query: str,
        limit: float | Omit = omit,
        threshold: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> KnowledgeSearchResponse:
        """
        Search across one or more knowledge collections using semantic similarity.

        The search uses vector embeddings to find the most relevant content. Results are
        ordered by relevance score (0-1, higher is more similar).

        Args:
          collection_ids: Collection IDs to search

          query: Natural language search query

          limit: Maximum number of results

          threshold: Minimum similarity score (0-1)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/knowledge/search",
            body=await async_maybe_transform(
                {
                    "collection_ids": collection_ids,
                    "query": query,
                    "limit": limit,
                    "threshold": threshold,
                },
                knowledge_search_params.KnowledgeSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=KnowledgeSearchResponse,
        )


class KnowledgeResourceWithRawResponse:
    def __init__(self, knowledge: KnowledgeResource) -> None:
        self._knowledge = knowledge

        self.search = to_raw_response_wrapper(
            knowledge.search,
        )

    @cached_property
    def collections(self) -> CollectionsResourceWithRawResponse:
        return CollectionsResourceWithRawResponse(self._knowledge.collections)


class AsyncKnowledgeResourceWithRawResponse:
    def __init__(self, knowledge: AsyncKnowledgeResource) -> None:
        self._knowledge = knowledge

        self.search = async_to_raw_response_wrapper(
            knowledge.search,
        )

    @cached_property
    def collections(self) -> AsyncCollectionsResourceWithRawResponse:
        return AsyncCollectionsResourceWithRawResponse(self._knowledge.collections)


class KnowledgeResourceWithStreamingResponse:
    def __init__(self, knowledge: KnowledgeResource) -> None:
        self._knowledge = knowledge

        self.search = to_streamed_response_wrapper(
            knowledge.search,
        )

    @cached_property
    def collections(self) -> CollectionsResourceWithStreamingResponse:
        return CollectionsResourceWithStreamingResponse(self._knowledge.collections)


class AsyncKnowledgeResourceWithStreamingResponse:
    def __init__(self, knowledge: AsyncKnowledgeResource) -> None:
        self._knowledge = knowledge

        self.search = async_to_streamed_response_wrapper(
            knowledge.search,
        )

    @cached_property
    def collections(self) -> AsyncCollectionsResourceWithStreamingResponse:
        return AsyncCollectionsResourceWithStreamingResponse(self._knowledge.collections)

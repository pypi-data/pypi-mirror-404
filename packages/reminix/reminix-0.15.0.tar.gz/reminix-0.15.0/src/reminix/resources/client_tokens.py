# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional

import httpx

from ..types import client_token_create_params
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
from ..types.client_token_create_response import ClientTokenCreateResponse

__all__ = ["ClientTokensResource", "AsyncClientTokensResource"]


class ClientTokensResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ClientTokensResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/reminix-ai/reminix-python#accessing-raw-response-data-eg-headers
        """
        return ClientTokensResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ClientTokensResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/reminix-ai/reminix-python#with_streaming_response
        """
        return ClientTokensResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        context: Dict[str, Optional[object]],
        server_context: Dict[str, Optional[object]] | Omit = omit,
        ttl_seconds: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ClientTokenCreateResponse:
        """
        Create a short-lived client token for browser SDK use.

        **Use case:** Your backend calls this endpoint to generate a token, then passes
        it to your frontend. The frontend uses the token to make authenticated requests
        to `/client/*` endpoints.

        **Context types:**

        - `context`: Public data accessible to the client via `/client/context`
        - `serverContext`: Private data only accessible to agents/handlers (never
          exposed to client)

        **Security:**

        - Tokens are short-lived (default 1 hour, max 24 hours)
        - Both context types are trusted and cannot be tampered with
        - Store the token securely - it will only be shown once

        **Example flow:**

        1. User logs in to your app
        2. Your backend calls `POST /v1/client-tokens` with
           `{ context: { userId: "user_123" }, serverContext: { internalId: "int_456" } }`
        3. Your backend returns the token to your frontend
        4. Frontend uses the token to call `/client/*` endpoints

        Args:
          context:
              Public context accessible to the client via /client/context (e.g., { userId:
              "...", sessionId: "..." })

          server_context: Private context only accessible to agents/handlers, never exposed to client
              (e.g., { internalId: "..." })

          ttl_seconds: Time-to-live in seconds. Default: 3600 (1 hour). Max: 86400 (24 hours).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/client-tokens",
            body=maybe_transform(
                {
                    "context": context,
                    "server_context": server_context,
                    "ttl_seconds": ttl_seconds,
                },
                client_token_create_params.ClientTokenCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ClientTokenCreateResponse,
        )

    def revoke(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Revoke a client token immediately.

        Once revoked, the token can no longer be used for authentication. This is a soft
        delete - the token record is kept for audit purposes.

        Args:
          id: Client token ID to revoke

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/client-tokens/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncClientTokensResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncClientTokensResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/reminix-ai/reminix-python#accessing-raw-response-data-eg-headers
        """
        return AsyncClientTokensResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncClientTokensResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/reminix-ai/reminix-python#with_streaming_response
        """
        return AsyncClientTokensResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        context: Dict[str, Optional[object]],
        server_context: Dict[str, Optional[object]] | Omit = omit,
        ttl_seconds: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ClientTokenCreateResponse:
        """
        Create a short-lived client token for browser SDK use.

        **Use case:** Your backend calls this endpoint to generate a token, then passes
        it to your frontend. The frontend uses the token to make authenticated requests
        to `/client/*` endpoints.

        **Context types:**

        - `context`: Public data accessible to the client via `/client/context`
        - `serverContext`: Private data only accessible to agents/handlers (never
          exposed to client)

        **Security:**

        - Tokens are short-lived (default 1 hour, max 24 hours)
        - Both context types are trusted and cannot be tampered with
        - Store the token securely - it will only be shown once

        **Example flow:**

        1. User logs in to your app
        2. Your backend calls `POST /v1/client-tokens` with
           `{ context: { userId: "user_123" }, serverContext: { internalId: "int_456" } }`
        3. Your backend returns the token to your frontend
        4. Frontend uses the token to call `/client/*` endpoints

        Args:
          context:
              Public context accessible to the client via /client/context (e.g., { userId:
              "...", sessionId: "..." })

          server_context: Private context only accessible to agents/handlers, never exposed to client
              (e.g., { internalId: "..." })

          ttl_seconds: Time-to-live in seconds. Default: 3600 (1 hour). Max: 86400 (24 hours).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/client-tokens",
            body=await async_maybe_transform(
                {
                    "context": context,
                    "server_context": server_context,
                    "ttl_seconds": ttl_seconds,
                },
                client_token_create_params.ClientTokenCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ClientTokenCreateResponse,
        )

    async def revoke(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Revoke a client token immediately.

        Once revoked, the token can no longer be used for authentication. This is a soft
        delete - the token record is kept for audit purposes.

        Args:
          id: Client token ID to revoke

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/client-tokens/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class ClientTokensResourceWithRawResponse:
    def __init__(self, client_tokens: ClientTokensResource) -> None:
        self._client_tokens = client_tokens

        self.create = to_raw_response_wrapper(
            client_tokens.create,
        )
        self.revoke = to_raw_response_wrapper(
            client_tokens.revoke,
        )


class AsyncClientTokensResourceWithRawResponse:
    def __init__(self, client_tokens: AsyncClientTokensResource) -> None:
        self._client_tokens = client_tokens

        self.create = async_to_raw_response_wrapper(
            client_tokens.create,
        )
        self.revoke = async_to_raw_response_wrapper(
            client_tokens.revoke,
        )


class ClientTokensResourceWithStreamingResponse:
    def __init__(self, client_tokens: ClientTokensResource) -> None:
        self._client_tokens = client_tokens

        self.create = to_streamed_response_wrapper(
            client_tokens.create,
        )
        self.revoke = to_streamed_response_wrapper(
            client_tokens.revoke,
        )


class AsyncClientTokensResourceWithStreamingResponse:
    def __init__(self, client_tokens: AsyncClientTokensResource) -> None:
        self._client_tokens = client_tokens

        self.create = async_to_streamed_response_wrapper(
            client_tokens.create,
        )
        self.revoke = async_to_streamed_response_wrapper(
            client_tokens.revoke,
        )

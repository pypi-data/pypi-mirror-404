# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from reminix import Reminix, AsyncReminix
from tests.utils import assert_matches_type
from reminix.types import ClientTokenCreateResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestClientTokens:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Reminix) -> None:
        client_token = client.client_tokens.create(
            context={
                "userId": "bar",
                "sessionId": "bar",
            },
        )
        assert_matches_type(ClientTokenCreateResponse, client_token, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Reminix) -> None:
        client_token = client.client_tokens.create(
            context={
                "userId": "bar",
                "sessionId": "bar",
            },
            server_context={"foo": "bar"},
            ttl_seconds=1,
        )
        assert_matches_type(ClientTokenCreateResponse, client_token, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Reminix) -> None:
        response = client.client_tokens.with_raw_response.create(
            context={
                "userId": "bar",
                "sessionId": "bar",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        client_token = response.parse()
        assert_matches_type(ClientTokenCreateResponse, client_token, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Reminix) -> None:
        with client.client_tokens.with_streaming_response.create(
            context={
                "userId": "bar",
                "sessionId": "bar",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            client_token = response.parse()
            assert_matches_type(ClientTokenCreateResponse, client_token, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_revoke(self, client: Reminix) -> None:
        client_token = client.client_tokens.revoke(
            "x",
        )
        assert client_token is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_revoke(self, client: Reminix) -> None:
        response = client.client_tokens.with_raw_response.revoke(
            "x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        client_token = response.parse()
        assert client_token is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_revoke(self, client: Reminix) -> None:
        with client.client_tokens.with_streaming_response.revoke(
            "x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            client_token = response.parse()
            assert client_token is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_revoke(self, client: Reminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.client_tokens.with_raw_response.revoke(
                "",
            )


class TestAsyncClientTokens:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncReminix) -> None:
        client_token = await async_client.client_tokens.create(
            context={
                "userId": "bar",
                "sessionId": "bar",
            },
        )
        assert_matches_type(ClientTokenCreateResponse, client_token, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncReminix) -> None:
        client_token = await async_client.client_tokens.create(
            context={
                "userId": "bar",
                "sessionId": "bar",
            },
            server_context={"foo": "bar"},
            ttl_seconds=1,
        )
        assert_matches_type(ClientTokenCreateResponse, client_token, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncReminix) -> None:
        response = await async_client.client_tokens.with_raw_response.create(
            context={
                "userId": "bar",
                "sessionId": "bar",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        client_token = await response.parse()
        assert_matches_type(ClientTokenCreateResponse, client_token, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncReminix) -> None:
        async with async_client.client_tokens.with_streaming_response.create(
            context={
                "userId": "bar",
                "sessionId": "bar",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            client_token = await response.parse()
            assert_matches_type(ClientTokenCreateResponse, client_token, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_revoke(self, async_client: AsyncReminix) -> None:
        client_token = await async_client.client_tokens.revoke(
            "x",
        )
        assert client_token is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_revoke(self, async_client: AsyncReminix) -> None:
        response = await async_client.client_tokens.with_raw_response.revoke(
            "x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        client_token = await response.parse()
        assert client_token is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_revoke(self, async_client: AsyncReminix) -> None:
        async with async_client.client_tokens.with_streaming_response.revoke(
            "x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            client_token = await response.parse()
            assert client_token is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_revoke(self, async_client: AsyncReminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.client_tokens.with_raw_response.revoke(
                "",
            )

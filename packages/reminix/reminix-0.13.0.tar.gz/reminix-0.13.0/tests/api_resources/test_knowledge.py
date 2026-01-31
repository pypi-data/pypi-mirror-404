# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from reminix import Reminix, AsyncReminix
from tests.utils import assert_matches_type
from reminix.types import KnowledgeSearchResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestKnowledge:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search(self, client: Reminix) -> None:
        knowledge = client.knowledge.search(
            collection_ids=["string"],
            query="x",
        )
        assert_matches_type(KnowledgeSearchResponse, knowledge, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search_with_all_params(self, client: Reminix) -> None:
        knowledge = client.knowledge.search(
            collection_ids=["string"],
            query="x",
            limit=1,
            threshold=0,
        )
        assert_matches_type(KnowledgeSearchResponse, knowledge, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_search(self, client: Reminix) -> None:
        response = client.knowledge.with_raw_response.search(
            collection_ids=["string"],
            query="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        knowledge = response.parse()
        assert_matches_type(KnowledgeSearchResponse, knowledge, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_search(self, client: Reminix) -> None:
        with client.knowledge.with_streaming_response.search(
            collection_ids=["string"],
            query="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            knowledge = response.parse()
            assert_matches_type(KnowledgeSearchResponse, knowledge, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncKnowledge:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search(self, async_client: AsyncReminix) -> None:
        knowledge = await async_client.knowledge.search(
            collection_ids=["string"],
            query="x",
        )
        assert_matches_type(KnowledgeSearchResponse, knowledge, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search_with_all_params(self, async_client: AsyncReminix) -> None:
        knowledge = await async_client.knowledge.search(
            collection_ids=["string"],
            query="x",
            limit=1,
            threshold=0,
        )
        assert_matches_type(KnowledgeSearchResponse, knowledge, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_search(self, async_client: AsyncReminix) -> None:
        response = await async_client.knowledge.with_raw_response.search(
            collection_ids=["string"],
            query="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        knowledge = await response.parse()
        assert_matches_type(KnowledgeSearchResponse, knowledge, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_search(self, async_client: AsyncReminix) -> None:
        async with async_client.knowledge.with_streaming_response.search(
            collection_ids=["string"],
            query="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            knowledge = await response.parse()
            assert_matches_type(KnowledgeSearchResponse, knowledge, path=["response"])

        assert cast(Any, response.is_closed) is True

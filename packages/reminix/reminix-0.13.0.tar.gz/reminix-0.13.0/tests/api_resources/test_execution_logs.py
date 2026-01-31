# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from reminix import Reminix, AsyncReminix
from tests.utils import assert_matches_type
from reminix.types import ExecutionLog
from reminix.pagination import SyncCursor, AsyncCursor

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestExecutionLogs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Reminix) -> None:
        execution_log = client.execution_logs.retrieve(
            "x",
        )
        assert_matches_type(ExecutionLog, execution_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Reminix) -> None:
        response = client.execution_logs.with_raw_response.retrieve(
            "x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        execution_log = response.parse()
        assert_matches_type(ExecutionLog, execution_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Reminix) -> None:
        with client.execution_logs.with_streaming_response.retrieve(
            "x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            execution_log = response.parse()
            assert_matches_type(ExecutionLog, execution_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Reminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.execution_logs.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Reminix) -> None:
        execution_log = client.execution_logs.list()
        assert_matches_type(SyncCursor[ExecutionLog], execution_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Reminix) -> None:
        execution_log = client.execution_logs.list(
            cursor="cursor",
            limit=1,
            name="name",
            source="api",
            status="success",
            type="agent_invoke",
        )
        assert_matches_type(SyncCursor[ExecutionLog], execution_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Reminix) -> None:
        response = client.execution_logs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        execution_log = response.parse()
        assert_matches_type(SyncCursor[ExecutionLog], execution_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Reminix) -> None:
        with client.execution_logs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            execution_log = response.parse()
            assert_matches_type(SyncCursor[ExecutionLog], execution_log, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncExecutionLogs:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncReminix) -> None:
        execution_log = await async_client.execution_logs.retrieve(
            "x",
        )
        assert_matches_type(ExecutionLog, execution_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncReminix) -> None:
        response = await async_client.execution_logs.with_raw_response.retrieve(
            "x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        execution_log = await response.parse()
        assert_matches_type(ExecutionLog, execution_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncReminix) -> None:
        async with async_client.execution_logs.with_streaming_response.retrieve(
            "x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            execution_log = await response.parse()
            assert_matches_type(ExecutionLog, execution_log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncReminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.execution_logs.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncReminix) -> None:
        execution_log = await async_client.execution_logs.list()
        assert_matches_type(AsyncCursor[ExecutionLog], execution_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncReminix) -> None:
        execution_log = await async_client.execution_logs.list(
            cursor="cursor",
            limit=1,
            name="name",
            source="api",
            status="success",
            type="agent_invoke",
        )
        assert_matches_type(AsyncCursor[ExecutionLog], execution_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncReminix) -> None:
        response = await async_client.execution_logs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        execution_log = await response.parse()
        assert_matches_type(AsyncCursor[ExecutionLog], execution_log, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncReminix) -> None:
        async with async_client.execution_logs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            execution_log = await response.parse()
            assert_matches_type(AsyncCursor[ExecutionLog], execution_log, path=["response"])

        assert cast(Any, response.is_closed) is True

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from reminix import Reminix, AsyncReminix
from tests.utils import assert_matches_type
from reminix.pagination import SyncCursor, AsyncCursor
from reminix.types.knowledge.collections import (
    KnowledgeDocument,
    DocumentUploadResponse,
    DocumentProcessResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDocuments:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Reminix) -> None:
        document = client.knowledge.collections.documents.retrieve(
            document_id="x",
            collection_id="x",
        )
        assert_matches_type(KnowledgeDocument, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Reminix) -> None:
        response = client.knowledge.collections.documents.with_raw_response.retrieve(
            document_id="x",
            collection_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(KnowledgeDocument, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Reminix) -> None:
        with client.knowledge.collections.documents.with_streaming_response.retrieve(
            document_id="x",
            collection_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(KnowledgeDocument, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Reminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `collection_id` but received ''"):
            client.knowledge.collections.documents.with_raw_response.retrieve(
                document_id="x",
                collection_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `document_id` but received ''"):
            client.knowledge.collections.documents.with_raw_response.retrieve(
                document_id="",
                collection_id="x",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Reminix) -> None:
        document = client.knowledge.collections.documents.list(
            id="x",
        )
        assert_matches_type(SyncCursor[KnowledgeDocument], document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Reminix) -> None:
        document = client.knowledge.collections.documents.list(
            id="x",
            cursor="cursor",
            limit=1,
            status="pending",
        )
        assert_matches_type(SyncCursor[KnowledgeDocument], document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Reminix) -> None:
        response = client.knowledge.collections.documents.with_raw_response.list(
            id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(SyncCursor[KnowledgeDocument], document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Reminix) -> None:
        with client.knowledge.collections.documents.with_streaming_response.list(
            id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(SyncCursor[KnowledgeDocument], document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: Reminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.knowledge.collections.documents.with_raw_response.list(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Reminix) -> None:
        document = client.knowledge.collections.documents.delete(
            document_id="x",
            collection_id="x",
        )
        assert document is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Reminix) -> None:
        response = client.knowledge.collections.documents.with_raw_response.delete(
            document_id="x",
            collection_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert document is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Reminix) -> None:
        with client.knowledge.collections.documents.with_streaming_response.delete(
            document_id="x",
            collection_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert document is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Reminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `collection_id` but received ''"):
            client.knowledge.collections.documents.with_raw_response.delete(
                document_id="x",
                collection_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `document_id` but received ''"):
            client.knowledge.collections.documents.with_raw_response.delete(
                document_id="",
                collection_id="x",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_process(self, client: Reminix) -> None:
        document = client.knowledge.collections.documents.process(
            document_id="x",
            collection_id="x",
        )
        assert_matches_type(DocumentProcessResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_process_with_all_params(self, client: Reminix) -> None:
        document = client.knowledge.collections.documents.process(
            document_id="x",
            collection_id="x",
            prefer_unstructured=True,
        )
        assert_matches_type(DocumentProcessResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_process(self, client: Reminix) -> None:
        response = client.knowledge.collections.documents.with_raw_response.process(
            document_id="x",
            collection_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentProcessResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_process(self, client: Reminix) -> None:
        with client.knowledge.collections.documents.with_streaming_response.process(
            document_id="x",
            collection_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentProcessResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_process(self, client: Reminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `collection_id` but received ''"):
            client.knowledge.collections.documents.with_raw_response.process(
                document_id="x",
                collection_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `document_id` but received ''"):
            client.knowledge.collections.documents.with_raw_response.process(
                document_id="",
                collection_id="x",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload(self, client: Reminix) -> None:
        document = client.knowledge.collections.documents.upload(
            id="x",
            mime_type="x",
            name="x",
        )
        assert_matches_type(DocumentUploadResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload_with_all_params(self, client: Reminix) -> None:
        document = client.knowledge.collections.documents.upload(
            id="x",
            mime_type="x",
            name="x",
            size=0,
        )
        assert_matches_type(DocumentUploadResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_upload(self, client: Reminix) -> None:
        response = client.knowledge.collections.documents.with_raw_response.upload(
            id="x",
            mime_type="x",
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = response.parse()
        assert_matches_type(DocumentUploadResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_upload(self, client: Reminix) -> None:
        with client.knowledge.collections.documents.with_streaming_response.upload(
            id="x",
            mime_type="x",
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = response.parse()
            assert_matches_type(DocumentUploadResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_upload(self, client: Reminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.knowledge.collections.documents.with_raw_response.upload(
                id="",
                mime_type="x",
                name="x",
            )


class TestAsyncDocuments:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncReminix) -> None:
        document = await async_client.knowledge.collections.documents.retrieve(
            document_id="x",
            collection_id="x",
        )
        assert_matches_type(KnowledgeDocument, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncReminix) -> None:
        response = await async_client.knowledge.collections.documents.with_raw_response.retrieve(
            document_id="x",
            collection_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(KnowledgeDocument, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncReminix) -> None:
        async with async_client.knowledge.collections.documents.with_streaming_response.retrieve(
            document_id="x",
            collection_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(KnowledgeDocument, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncReminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `collection_id` but received ''"):
            await async_client.knowledge.collections.documents.with_raw_response.retrieve(
                document_id="x",
                collection_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `document_id` but received ''"):
            await async_client.knowledge.collections.documents.with_raw_response.retrieve(
                document_id="",
                collection_id="x",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncReminix) -> None:
        document = await async_client.knowledge.collections.documents.list(
            id="x",
        )
        assert_matches_type(AsyncCursor[KnowledgeDocument], document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncReminix) -> None:
        document = await async_client.knowledge.collections.documents.list(
            id="x",
            cursor="cursor",
            limit=1,
            status="pending",
        )
        assert_matches_type(AsyncCursor[KnowledgeDocument], document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncReminix) -> None:
        response = await async_client.knowledge.collections.documents.with_raw_response.list(
            id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(AsyncCursor[KnowledgeDocument], document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncReminix) -> None:
        async with async_client.knowledge.collections.documents.with_streaming_response.list(
            id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(AsyncCursor[KnowledgeDocument], document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncReminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.knowledge.collections.documents.with_raw_response.list(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncReminix) -> None:
        document = await async_client.knowledge.collections.documents.delete(
            document_id="x",
            collection_id="x",
        )
        assert document is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncReminix) -> None:
        response = await async_client.knowledge.collections.documents.with_raw_response.delete(
            document_id="x",
            collection_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert document is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncReminix) -> None:
        async with async_client.knowledge.collections.documents.with_streaming_response.delete(
            document_id="x",
            collection_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert document is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncReminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `collection_id` but received ''"):
            await async_client.knowledge.collections.documents.with_raw_response.delete(
                document_id="x",
                collection_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `document_id` but received ''"):
            await async_client.knowledge.collections.documents.with_raw_response.delete(
                document_id="",
                collection_id="x",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_process(self, async_client: AsyncReminix) -> None:
        document = await async_client.knowledge.collections.documents.process(
            document_id="x",
            collection_id="x",
        )
        assert_matches_type(DocumentProcessResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_process_with_all_params(self, async_client: AsyncReminix) -> None:
        document = await async_client.knowledge.collections.documents.process(
            document_id="x",
            collection_id="x",
            prefer_unstructured=True,
        )
        assert_matches_type(DocumentProcessResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_process(self, async_client: AsyncReminix) -> None:
        response = await async_client.knowledge.collections.documents.with_raw_response.process(
            document_id="x",
            collection_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentProcessResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_process(self, async_client: AsyncReminix) -> None:
        async with async_client.knowledge.collections.documents.with_streaming_response.process(
            document_id="x",
            collection_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentProcessResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_process(self, async_client: AsyncReminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `collection_id` but received ''"):
            await async_client.knowledge.collections.documents.with_raw_response.process(
                document_id="x",
                collection_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `document_id` but received ''"):
            await async_client.knowledge.collections.documents.with_raw_response.process(
                document_id="",
                collection_id="x",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload(self, async_client: AsyncReminix) -> None:
        document = await async_client.knowledge.collections.documents.upload(
            id="x",
            mime_type="x",
            name="x",
        )
        assert_matches_type(DocumentUploadResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload_with_all_params(self, async_client: AsyncReminix) -> None:
        document = await async_client.knowledge.collections.documents.upload(
            id="x",
            mime_type="x",
            name="x",
            size=0,
        )
        assert_matches_type(DocumentUploadResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_upload(self, async_client: AsyncReminix) -> None:
        response = await async_client.knowledge.collections.documents.with_raw_response.upload(
            id="x",
            mime_type="x",
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        document = await response.parse()
        assert_matches_type(DocumentUploadResponse, document, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_upload(self, async_client: AsyncReminix) -> None:
        async with async_client.knowledge.collections.documents.with_streaming_response.upload(
            id="x",
            mime_type="x",
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            document = await response.parse()
            assert_matches_type(DocumentUploadResponse, document, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_upload(self, async_client: AsyncReminix) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.knowledge.collections.documents.with_raw_response.upload(
                id="",
                mime_type="x",
                name="x",
            )

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Mapping
from typing_extensions import Self, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    Omit,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
    not_given,
)
from ._utils import is_given, get_async_library
from ._compat import cached_property
from ._version import __version__
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import ReminixError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import tools, agents, memory, projects, knowledge, client_tokens, conversations, execution_logs
    from .resources.tools import ToolsResource, AsyncToolsResource
    from .resources.agents import AgentsResource, AsyncAgentsResource
    from .resources.memory import MemoryResource, AsyncMemoryResource
    from .resources.projects import ProjectsResource, AsyncProjectsResource
    from .resources.client_tokens import ClientTokensResource, AsyncClientTokensResource
    from .resources.conversations import ConversationsResource, AsyncConversationsResource
    from .resources.execution_logs import ExecutionLogsResource, AsyncExecutionLogsResource
    from .resources.knowledge.knowledge import KnowledgeResource, AsyncKnowledgeResource

__all__ = ["Timeout", "Transport", "ProxiesTypes", "RequestOptions", "Reminix", "AsyncReminix", "Client", "AsyncClient"]


class Reminix(SyncAPIClient):
    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new synchronous Reminix client instance.

        This automatically infers the `api_key` argument from the `REMINIX_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("REMINIX_API_KEY")
        if api_key is None:
            raise ReminixError(
                "The api_key client option must be set either by passing api_key to the client or by setting the REMINIX_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("REMINIX_BASE_URL")
        if base_url is None:
            base_url = f"https://api.reminix.com/v1"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def projects(self) -> ProjectsResource:
        from .resources.projects import ProjectsResource

        return ProjectsResource(self)

    @cached_property
    def agents(self) -> AgentsResource:
        from .resources.agents import AgentsResource

        return AgentsResource(self)

    @cached_property
    def tools(self) -> ToolsResource:
        from .resources.tools import ToolsResource

        return ToolsResource(self)

    @cached_property
    def client_tokens(self) -> ClientTokensResource:
        from .resources.client_tokens import ClientTokensResource

        return ClientTokensResource(self)

    @cached_property
    def execution_logs(self) -> ExecutionLogsResource:
        from .resources.execution_logs import ExecutionLogsResource

        return ExecutionLogsResource(self)

    @cached_property
    def conversations(self) -> ConversationsResource:
        from .resources.conversations import ConversationsResource

        return ConversationsResource(self)

    @cached_property
    def memory(self) -> MemoryResource:
        from .resources.memory import MemoryResource

        return MemoryResource(self)

    @cached_property
    def knowledge(self) -> KnowledgeResource:
        from .resources.knowledge import KnowledgeResource

        return KnowledgeResource(self)

    @cached_property
    def with_raw_response(self) -> ReminixWithRawResponse:
        return ReminixWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ReminixWithStreamedResponse:
        return ReminixWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            "X-Reminix-Source": "sdk",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class AsyncReminix(AsyncAPIClient):
    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new async AsyncReminix client instance.

        This automatically infers the `api_key` argument from the `REMINIX_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("REMINIX_API_KEY")
        if api_key is None:
            raise ReminixError(
                "The api_key client option must be set either by passing api_key to the client or by setting the REMINIX_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("REMINIX_BASE_URL")
        if base_url is None:
            base_url = f"https://api.reminix.com/v1"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def projects(self) -> AsyncProjectsResource:
        from .resources.projects import AsyncProjectsResource

        return AsyncProjectsResource(self)

    @cached_property
    def agents(self) -> AsyncAgentsResource:
        from .resources.agents import AsyncAgentsResource

        return AsyncAgentsResource(self)

    @cached_property
    def tools(self) -> AsyncToolsResource:
        from .resources.tools import AsyncToolsResource

        return AsyncToolsResource(self)

    @cached_property
    def client_tokens(self) -> AsyncClientTokensResource:
        from .resources.client_tokens import AsyncClientTokensResource

        return AsyncClientTokensResource(self)

    @cached_property
    def execution_logs(self) -> AsyncExecutionLogsResource:
        from .resources.execution_logs import AsyncExecutionLogsResource

        return AsyncExecutionLogsResource(self)

    @cached_property
    def conversations(self) -> AsyncConversationsResource:
        from .resources.conversations import AsyncConversationsResource

        return AsyncConversationsResource(self)

    @cached_property
    def memory(self) -> AsyncMemoryResource:
        from .resources.memory import AsyncMemoryResource

        return AsyncMemoryResource(self)

    @cached_property
    def knowledge(self) -> AsyncKnowledgeResource:
        from .resources.knowledge import AsyncKnowledgeResource

        return AsyncKnowledgeResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncReminixWithRawResponse:
        return AsyncReminixWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncReminixWithStreamedResponse:
        return AsyncReminixWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            "X-Reminix-Source": "sdk",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class ReminixWithRawResponse:
    _client: Reminix

    def __init__(self, client: Reminix) -> None:
        self._client = client

    @cached_property
    def projects(self) -> projects.ProjectsResourceWithRawResponse:
        from .resources.projects import ProjectsResourceWithRawResponse

        return ProjectsResourceWithRawResponse(self._client.projects)

    @cached_property
    def agents(self) -> agents.AgentsResourceWithRawResponse:
        from .resources.agents import AgentsResourceWithRawResponse

        return AgentsResourceWithRawResponse(self._client.agents)

    @cached_property
    def tools(self) -> tools.ToolsResourceWithRawResponse:
        from .resources.tools import ToolsResourceWithRawResponse

        return ToolsResourceWithRawResponse(self._client.tools)

    @cached_property
    def client_tokens(self) -> client_tokens.ClientTokensResourceWithRawResponse:
        from .resources.client_tokens import ClientTokensResourceWithRawResponse

        return ClientTokensResourceWithRawResponse(self._client.client_tokens)

    @cached_property
    def execution_logs(self) -> execution_logs.ExecutionLogsResourceWithRawResponse:
        from .resources.execution_logs import ExecutionLogsResourceWithRawResponse

        return ExecutionLogsResourceWithRawResponse(self._client.execution_logs)

    @cached_property
    def conversations(self) -> conversations.ConversationsResourceWithRawResponse:
        from .resources.conversations import ConversationsResourceWithRawResponse

        return ConversationsResourceWithRawResponse(self._client.conversations)

    @cached_property
    def memory(self) -> memory.MemoryResourceWithRawResponse:
        from .resources.memory import MemoryResourceWithRawResponse

        return MemoryResourceWithRawResponse(self._client.memory)

    @cached_property
    def knowledge(self) -> knowledge.KnowledgeResourceWithRawResponse:
        from .resources.knowledge import KnowledgeResourceWithRawResponse

        return KnowledgeResourceWithRawResponse(self._client.knowledge)


class AsyncReminixWithRawResponse:
    _client: AsyncReminix

    def __init__(self, client: AsyncReminix) -> None:
        self._client = client

    @cached_property
    def projects(self) -> projects.AsyncProjectsResourceWithRawResponse:
        from .resources.projects import AsyncProjectsResourceWithRawResponse

        return AsyncProjectsResourceWithRawResponse(self._client.projects)

    @cached_property
    def agents(self) -> agents.AsyncAgentsResourceWithRawResponse:
        from .resources.agents import AsyncAgentsResourceWithRawResponse

        return AsyncAgentsResourceWithRawResponse(self._client.agents)

    @cached_property
    def tools(self) -> tools.AsyncToolsResourceWithRawResponse:
        from .resources.tools import AsyncToolsResourceWithRawResponse

        return AsyncToolsResourceWithRawResponse(self._client.tools)

    @cached_property
    def client_tokens(self) -> client_tokens.AsyncClientTokensResourceWithRawResponse:
        from .resources.client_tokens import AsyncClientTokensResourceWithRawResponse

        return AsyncClientTokensResourceWithRawResponse(self._client.client_tokens)

    @cached_property
    def execution_logs(self) -> execution_logs.AsyncExecutionLogsResourceWithRawResponse:
        from .resources.execution_logs import AsyncExecutionLogsResourceWithRawResponse

        return AsyncExecutionLogsResourceWithRawResponse(self._client.execution_logs)

    @cached_property
    def conversations(self) -> conversations.AsyncConversationsResourceWithRawResponse:
        from .resources.conversations import AsyncConversationsResourceWithRawResponse

        return AsyncConversationsResourceWithRawResponse(self._client.conversations)

    @cached_property
    def memory(self) -> memory.AsyncMemoryResourceWithRawResponse:
        from .resources.memory import AsyncMemoryResourceWithRawResponse

        return AsyncMemoryResourceWithRawResponse(self._client.memory)

    @cached_property
    def knowledge(self) -> knowledge.AsyncKnowledgeResourceWithRawResponse:
        from .resources.knowledge import AsyncKnowledgeResourceWithRawResponse

        return AsyncKnowledgeResourceWithRawResponse(self._client.knowledge)


class ReminixWithStreamedResponse:
    _client: Reminix

    def __init__(self, client: Reminix) -> None:
        self._client = client

    @cached_property
    def projects(self) -> projects.ProjectsResourceWithStreamingResponse:
        from .resources.projects import ProjectsResourceWithStreamingResponse

        return ProjectsResourceWithStreamingResponse(self._client.projects)

    @cached_property
    def agents(self) -> agents.AgentsResourceWithStreamingResponse:
        from .resources.agents import AgentsResourceWithStreamingResponse

        return AgentsResourceWithStreamingResponse(self._client.agents)

    @cached_property
    def tools(self) -> tools.ToolsResourceWithStreamingResponse:
        from .resources.tools import ToolsResourceWithStreamingResponse

        return ToolsResourceWithStreamingResponse(self._client.tools)

    @cached_property
    def client_tokens(self) -> client_tokens.ClientTokensResourceWithStreamingResponse:
        from .resources.client_tokens import ClientTokensResourceWithStreamingResponse

        return ClientTokensResourceWithStreamingResponse(self._client.client_tokens)

    @cached_property
    def execution_logs(self) -> execution_logs.ExecutionLogsResourceWithStreamingResponse:
        from .resources.execution_logs import ExecutionLogsResourceWithStreamingResponse

        return ExecutionLogsResourceWithStreamingResponse(self._client.execution_logs)

    @cached_property
    def conversations(self) -> conversations.ConversationsResourceWithStreamingResponse:
        from .resources.conversations import ConversationsResourceWithStreamingResponse

        return ConversationsResourceWithStreamingResponse(self._client.conversations)

    @cached_property
    def memory(self) -> memory.MemoryResourceWithStreamingResponse:
        from .resources.memory import MemoryResourceWithStreamingResponse

        return MemoryResourceWithStreamingResponse(self._client.memory)

    @cached_property
    def knowledge(self) -> knowledge.KnowledgeResourceWithStreamingResponse:
        from .resources.knowledge import KnowledgeResourceWithStreamingResponse

        return KnowledgeResourceWithStreamingResponse(self._client.knowledge)


class AsyncReminixWithStreamedResponse:
    _client: AsyncReminix

    def __init__(self, client: AsyncReminix) -> None:
        self._client = client

    @cached_property
    def projects(self) -> projects.AsyncProjectsResourceWithStreamingResponse:
        from .resources.projects import AsyncProjectsResourceWithStreamingResponse

        return AsyncProjectsResourceWithStreamingResponse(self._client.projects)

    @cached_property
    def agents(self) -> agents.AsyncAgentsResourceWithStreamingResponse:
        from .resources.agents import AsyncAgentsResourceWithStreamingResponse

        return AsyncAgentsResourceWithStreamingResponse(self._client.agents)

    @cached_property
    def tools(self) -> tools.AsyncToolsResourceWithStreamingResponse:
        from .resources.tools import AsyncToolsResourceWithStreamingResponse

        return AsyncToolsResourceWithStreamingResponse(self._client.tools)

    @cached_property
    def client_tokens(self) -> client_tokens.AsyncClientTokensResourceWithStreamingResponse:
        from .resources.client_tokens import AsyncClientTokensResourceWithStreamingResponse

        return AsyncClientTokensResourceWithStreamingResponse(self._client.client_tokens)

    @cached_property
    def execution_logs(self) -> execution_logs.AsyncExecutionLogsResourceWithStreamingResponse:
        from .resources.execution_logs import AsyncExecutionLogsResourceWithStreamingResponse

        return AsyncExecutionLogsResourceWithStreamingResponse(self._client.execution_logs)

    @cached_property
    def conversations(self) -> conversations.AsyncConversationsResourceWithStreamingResponse:
        from .resources.conversations import AsyncConversationsResourceWithStreamingResponse

        return AsyncConversationsResourceWithStreamingResponse(self._client.conversations)

    @cached_property
    def memory(self) -> memory.AsyncMemoryResourceWithStreamingResponse:
        from .resources.memory import AsyncMemoryResourceWithStreamingResponse

        return AsyncMemoryResourceWithStreamingResponse(self._client.memory)

    @cached_property
    def knowledge(self) -> knowledge.AsyncKnowledgeResourceWithStreamingResponse:
        from .resources.knowledge import AsyncKnowledgeResourceWithStreamingResponse

        return AsyncKnowledgeResourceWithStreamingResponse(self._client.knowledge)


Client = Reminix

AsyncClient = AsyncReminix

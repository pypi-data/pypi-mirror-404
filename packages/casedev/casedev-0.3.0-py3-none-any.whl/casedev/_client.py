# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Dict, Mapping, cast
from typing_extensions import Self, Literal, override

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
from ._exceptions import CasedevError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import llm, ocr, vault, voice, format, search, compute
    from .resources.llm.llm import LlmResource, AsyncLlmResource
    from .resources.ocr.ocr import OcrResource, AsyncOcrResource
    from .resources.vault.vault import VaultResource, AsyncVaultResource
    from .resources.voice.voice import VoiceResource, AsyncVoiceResource
    from .resources.format.format import FormatResource, AsyncFormatResource
    from .resources.search.search import SearchResource, AsyncSearchResource
    from .resources.compute.compute import ComputeResource, AsyncComputeResource

__all__ = [
    "ENVIRONMENTS",
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "Casedev",
    "AsyncCasedev",
    "Client",
    "AsyncClient",
]

ENVIRONMENTS: Dict[str, str] = {
    "production": "https://api.case.dev",
    "local": "http://localhost:2728",
}


class Casedev(SyncAPIClient):
    # client options
    api_key: str

    _environment: Literal["production", "local"] | NotGiven

    def __init__(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "local"] | NotGiven = not_given,
        base_url: str | httpx.URL | None | NotGiven = not_given,
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
        """Construct a new synchronous Casedev client instance.

        This automatically infers the `api_key` argument from the `CASEDEV_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("CASEDEV_API_KEY")
        if api_key is None:
            raise CasedevError(
                "The api_key client option must be set either by passing api_key to the client or by setting the CASEDEV_API_KEY environment variable"
            )
        self.api_key = api_key

        self._environment = environment

        base_url_env = os.environ.get("CASEDEV_BASE_URL")
        if is_given(base_url) and base_url is not None:
            # cast required because mypy doesn't understand the type narrowing
            base_url = cast("str | httpx.URL", base_url)  # pyright: ignore[reportUnnecessaryCast]
        elif is_given(environment):
            if base_url_env and base_url is not None:
                raise ValueError(
                    "Ambiguous URL; The `CASEDEV_BASE_URL` env var and the `environment` argument are given. If you want to use the environment, you must pass base_url=None",
                )

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc
        elif base_url_env is not None:
            base_url = base_url_env
        else:
            self._environment = environment = "production"

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc

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
    def compute(self) -> ComputeResource:
        from .resources.compute import ComputeResource

        return ComputeResource(self)

    @cached_property
    def format(self) -> FormatResource:
        from .resources.format import FormatResource

        return FormatResource(self)

    @cached_property
    def llm(self) -> LlmResource:
        from .resources.llm import LlmResource

        return LlmResource(self)

    @cached_property
    def ocr(self) -> OcrResource:
        from .resources.ocr import OcrResource

        return OcrResource(self)

    @cached_property
    def search(self) -> SearchResource:
        from .resources.search import SearchResource

        return SearchResource(self)

    @cached_property
    def vault(self) -> VaultResource:
        from .resources.vault import VaultResource

        return VaultResource(self)

    @cached_property
    def voice(self) -> VoiceResource:
        from .resources.voice import VoiceResource

        return VoiceResource(self)

    @cached_property
    def with_raw_response(self) -> CasedevWithRawResponse:
        return CasedevWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CasedevWithStreamedResponse:
        return CasedevWithStreamedResponse(self)

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
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "local"] | None = None,
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
            environment=environment or self._environment,
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


class AsyncCasedev(AsyncAPIClient):
    # client options
    api_key: str

    _environment: Literal["production", "local"] | NotGiven

    def __init__(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "local"] | NotGiven = not_given,
        base_url: str | httpx.URL | None | NotGiven = not_given,
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
        """Construct a new async AsyncCasedev client instance.

        This automatically infers the `api_key` argument from the `CASEDEV_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("CASEDEV_API_KEY")
        if api_key is None:
            raise CasedevError(
                "The api_key client option must be set either by passing api_key to the client or by setting the CASEDEV_API_KEY environment variable"
            )
        self.api_key = api_key

        self._environment = environment

        base_url_env = os.environ.get("CASEDEV_BASE_URL")
        if is_given(base_url) and base_url is not None:
            # cast required because mypy doesn't understand the type narrowing
            base_url = cast("str | httpx.URL", base_url)  # pyright: ignore[reportUnnecessaryCast]
        elif is_given(environment):
            if base_url_env and base_url is not None:
                raise ValueError(
                    "Ambiguous URL; The `CASEDEV_BASE_URL` env var and the `environment` argument are given. If you want to use the environment, you must pass base_url=None",
                )

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc
        elif base_url_env is not None:
            base_url = base_url_env
        else:
            self._environment = environment = "production"

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc

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
    def compute(self) -> AsyncComputeResource:
        from .resources.compute import AsyncComputeResource

        return AsyncComputeResource(self)

    @cached_property
    def format(self) -> AsyncFormatResource:
        from .resources.format import AsyncFormatResource

        return AsyncFormatResource(self)

    @cached_property
    def llm(self) -> AsyncLlmResource:
        from .resources.llm import AsyncLlmResource

        return AsyncLlmResource(self)

    @cached_property
    def ocr(self) -> AsyncOcrResource:
        from .resources.ocr import AsyncOcrResource

        return AsyncOcrResource(self)

    @cached_property
    def search(self) -> AsyncSearchResource:
        from .resources.search import AsyncSearchResource

        return AsyncSearchResource(self)

    @cached_property
    def vault(self) -> AsyncVaultResource:
        from .resources.vault import AsyncVaultResource

        return AsyncVaultResource(self)

    @cached_property
    def voice(self) -> AsyncVoiceResource:
        from .resources.voice import AsyncVoiceResource

        return AsyncVoiceResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncCasedevWithRawResponse:
        return AsyncCasedevWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCasedevWithStreamedResponse:
        return AsyncCasedevWithStreamedResponse(self)

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
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "local"] | None = None,
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
            environment=environment or self._environment,
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


class CasedevWithRawResponse:
    _client: Casedev

    def __init__(self, client: Casedev) -> None:
        self._client = client

    @cached_property
    def compute(self) -> compute.ComputeResourceWithRawResponse:
        from .resources.compute import ComputeResourceWithRawResponse

        return ComputeResourceWithRawResponse(self._client.compute)

    @cached_property
    def format(self) -> format.FormatResourceWithRawResponse:
        from .resources.format import FormatResourceWithRawResponse

        return FormatResourceWithRawResponse(self._client.format)

    @cached_property
    def llm(self) -> llm.LlmResourceWithRawResponse:
        from .resources.llm import LlmResourceWithRawResponse

        return LlmResourceWithRawResponse(self._client.llm)

    @cached_property
    def ocr(self) -> ocr.OcrResourceWithRawResponse:
        from .resources.ocr import OcrResourceWithRawResponse

        return OcrResourceWithRawResponse(self._client.ocr)

    @cached_property
    def search(self) -> search.SearchResourceWithRawResponse:
        from .resources.search import SearchResourceWithRawResponse

        return SearchResourceWithRawResponse(self._client.search)

    @cached_property
    def vault(self) -> vault.VaultResourceWithRawResponse:
        from .resources.vault import VaultResourceWithRawResponse

        return VaultResourceWithRawResponse(self._client.vault)

    @cached_property
    def voice(self) -> voice.VoiceResourceWithRawResponse:
        from .resources.voice import VoiceResourceWithRawResponse

        return VoiceResourceWithRawResponse(self._client.voice)


class AsyncCasedevWithRawResponse:
    _client: AsyncCasedev

    def __init__(self, client: AsyncCasedev) -> None:
        self._client = client

    @cached_property
    def compute(self) -> compute.AsyncComputeResourceWithRawResponse:
        from .resources.compute import AsyncComputeResourceWithRawResponse

        return AsyncComputeResourceWithRawResponse(self._client.compute)

    @cached_property
    def format(self) -> format.AsyncFormatResourceWithRawResponse:
        from .resources.format import AsyncFormatResourceWithRawResponse

        return AsyncFormatResourceWithRawResponse(self._client.format)

    @cached_property
    def llm(self) -> llm.AsyncLlmResourceWithRawResponse:
        from .resources.llm import AsyncLlmResourceWithRawResponse

        return AsyncLlmResourceWithRawResponse(self._client.llm)

    @cached_property
    def ocr(self) -> ocr.AsyncOcrResourceWithRawResponse:
        from .resources.ocr import AsyncOcrResourceWithRawResponse

        return AsyncOcrResourceWithRawResponse(self._client.ocr)

    @cached_property
    def search(self) -> search.AsyncSearchResourceWithRawResponse:
        from .resources.search import AsyncSearchResourceWithRawResponse

        return AsyncSearchResourceWithRawResponse(self._client.search)

    @cached_property
    def vault(self) -> vault.AsyncVaultResourceWithRawResponse:
        from .resources.vault import AsyncVaultResourceWithRawResponse

        return AsyncVaultResourceWithRawResponse(self._client.vault)

    @cached_property
    def voice(self) -> voice.AsyncVoiceResourceWithRawResponse:
        from .resources.voice import AsyncVoiceResourceWithRawResponse

        return AsyncVoiceResourceWithRawResponse(self._client.voice)


class CasedevWithStreamedResponse:
    _client: Casedev

    def __init__(self, client: Casedev) -> None:
        self._client = client

    @cached_property
    def compute(self) -> compute.ComputeResourceWithStreamingResponse:
        from .resources.compute import ComputeResourceWithStreamingResponse

        return ComputeResourceWithStreamingResponse(self._client.compute)

    @cached_property
    def format(self) -> format.FormatResourceWithStreamingResponse:
        from .resources.format import FormatResourceWithStreamingResponse

        return FormatResourceWithStreamingResponse(self._client.format)

    @cached_property
    def llm(self) -> llm.LlmResourceWithStreamingResponse:
        from .resources.llm import LlmResourceWithStreamingResponse

        return LlmResourceWithStreamingResponse(self._client.llm)

    @cached_property
    def ocr(self) -> ocr.OcrResourceWithStreamingResponse:
        from .resources.ocr import OcrResourceWithStreamingResponse

        return OcrResourceWithStreamingResponse(self._client.ocr)

    @cached_property
    def search(self) -> search.SearchResourceWithStreamingResponse:
        from .resources.search import SearchResourceWithStreamingResponse

        return SearchResourceWithStreamingResponse(self._client.search)

    @cached_property
    def vault(self) -> vault.VaultResourceWithStreamingResponse:
        from .resources.vault import VaultResourceWithStreamingResponse

        return VaultResourceWithStreamingResponse(self._client.vault)

    @cached_property
    def voice(self) -> voice.VoiceResourceWithStreamingResponse:
        from .resources.voice import VoiceResourceWithStreamingResponse

        return VoiceResourceWithStreamingResponse(self._client.voice)


class AsyncCasedevWithStreamedResponse:
    _client: AsyncCasedev

    def __init__(self, client: AsyncCasedev) -> None:
        self._client = client

    @cached_property
    def compute(self) -> compute.AsyncComputeResourceWithStreamingResponse:
        from .resources.compute import AsyncComputeResourceWithStreamingResponse

        return AsyncComputeResourceWithStreamingResponse(self._client.compute)

    @cached_property
    def format(self) -> format.AsyncFormatResourceWithStreamingResponse:
        from .resources.format import AsyncFormatResourceWithStreamingResponse

        return AsyncFormatResourceWithStreamingResponse(self._client.format)

    @cached_property
    def llm(self) -> llm.AsyncLlmResourceWithStreamingResponse:
        from .resources.llm import AsyncLlmResourceWithStreamingResponse

        return AsyncLlmResourceWithStreamingResponse(self._client.llm)

    @cached_property
    def ocr(self) -> ocr.AsyncOcrResourceWithStreamingResponse:
        from .resources.ocr import AsyncOcrResourceWithStreamingResponse

        return AsyncOcrResourceWithStreamingResponse(self._client.ocr)

    @cached_property
    def search(self) -> search.AsyncSearchResourceWithStreamingResponse:
        from .resources.search import AsyncSearchResourceWithStreamingResponse

        return AsyncSearchResourceWithStreamingResponse(self._client.search)

    @cached_property
    def vault(self) -> vault.AsyncVaultResourceWithStreamingResponse:
        from .resources.vault import AsyncVaultResourceWithStreamingResponse

        return AsyncVaultResourceWithStreamingResponse(self._client.vault)

    @cached_property
    def voice(self) -> voice.AsyncVoiceResourceWithStreamingResponse:
        from .resources.voice import AsyncVoiceResourceWithStreamingResponse

        return AsyncVoiceResourceWithStreamingResponse(self._client.voice)


Client = Casedev

AsyncClient = AsyncCasedev

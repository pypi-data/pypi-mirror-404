"""Xeno API Client"""

import os
from typing import Optional, Dict, Any, Union, Iterator, AsyncIterator
import httpx

from xeno.resources.image import ImageResource, AsyncImageResource
from xeno.resources.video import VideoResource, AsyncVideoResource
from xeno.resources.music import MusicResource, AsyncMusicResource
from xeno.resources.chat import ChatResource, AsyncChatResource
from xeno.resources.models import ModelsResource, AsyncModelsResource
from xeno.exceptions import (
    XenoError,
    AuthenticationError,
    RateLimitError,
    APIError,
    InvalidRequestError,
    InsufficientCreditsError,
)


DEFAULT_BASE_URL = "https://api.xeno-studio.com/v1"
DEFAULT_TIMEOUT = 60.0


class BaseClient:
    """Base client with shared functionality"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 2,
    ):
        self.api_key = api_key or os.environ.get("XENO_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key is required. Pass api_key parameter or set XENO_API_KEY environment variable."
            )

        self.base_url = (base_url or os.environ.get("XENO_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "xeno-python/0.1.0",
        }

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the API"""
        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", response.text)
            error_type = error_data.get("error", {}).get("type", "api_error")
        except Exception:
            error_message = response.text
            error_type = "api_error"

        status_code = response.status_code

        if status_code == 401:
            raise AuthenticationError(error_message, status_code)
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                error_message,
                status_code,
                retry_after=int(retry_after) if retry_after else None,
            )
        elif status_code == 400:
            raise InvalidRequestError(error_message, status_code)
        elif status_code == 402:
            raise InsufficientCreditsError(error_message, status_code)
        else:
            raise APIError(error_message, status_code)


class Client(BaseClient):
    """
    Synchronous Xeno API client.

    Usage:
        client = xeno.Client(api_key="your-api-key")

        # Generate an image
        image = client.image.generate(model="flux-pro-1.1", prompt="A sunset")
        print(image.url)

        # Chat completion
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 2,
    ):
        super().__init__(api_key, base_url, timeout, max_retries)

        self._client = httpx.Client(
            base_url=self.base_url,
            headers=self._get_headers(),
            timeout=timeout,
        )

        # Initialize resources
        self.image = ImageResource(self)
        self.video = VideoResource(self)
        self.music = MusicResource(self)
        self.chat = ChatResource(self)
        self.models = ModelsResource(self)

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> Union[Dict[str, Any], Iterator[bytes]]:
        """Make a request to the API"""
        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.request(
                    method=method,
                    url=path,
                    json=json,
                    params=params,
                )

                if response.status_code >= 400:
                    self._handle_error_response(response)

                if stream:
                    return response.iter_lines()

                return response.json()

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt == self.max_retries:
                    raise XenoError(f"Connection error: {str(e)}")
                continue

    def close(self) -> None:
        """Close the client"""
        self._client.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncClient(BaseClient):
    """
    Asynchronous Xeno API client.

    Usage:
        async with xeno.AsyncClient(api_key="your-api-key") as client:
            image = await client.image.generate(model="flux-pro-1.1", prompt="A sunset")
            print(image.url)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 2,
    ):
        super().__init__(api_key, base_url, timeout, max_retries)

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._get_headers(),
            timeout=timeout,
        )

        # Initialize resources
        self.image = AsyncImageResource(self)
        self.video = AsyncVideoResource(self)
        self.music = AsyncMusicResource(self)
        self.chat = AsyncChatResource(self)
        self.models = AsyncModelsResource(self)

    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> Union[Dict[str, Any], AsyncIterator[bytes]]:
        """Make an async request to the API"""
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=path,
                    json=json,
                    params=params,
                )

                if response.status_code >= 400:
                    self._handle_error_response(response)

                if stream:
                    return response.aiter_lines()

                return response.json()

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt == self.max_retries:
                    raise XenoError(f"Connection error: {str(e)}")
                continue

    async def close(self) -> None:
        """Close the client"""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

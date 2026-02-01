"""Models resource"""

from typing import Optional, TYPE_CHECKING, List
from xeno._types.responses import Model, ModelList

if TYPE_CHECKING:
    from xeno.client import Client, AsyncClient


class ModelsResource:
    """
    Models resource.

    Usage:
        models = client.models.list()
        for model in models.data:
            print(model.id)
    """

    def __init__(self, client: "Client"):
        self._client = client

    def list(self) -> ModelList:
        """
        List all available models.

        Returns:
            ModelList with all available models
        """
        response = self._client._request("GET", "/models")
        return ModelList(**response)

    def retrieve(self, model_id: str) -> Model:
        """
        Get details about a specific model.

        Args:
            model_id: The model ID to retrieve

        Returns:
            Model with details
        """
        response = self._client._request("GET", f"/models/{model_id}")
        return Model(**response)


class AsyncModelsResource:
    """Async models resource"""

    def __init__(self, client: "AsyncClient"):
        self._client = client

    async def list(self) -> ModelList:
        """List all available models (async)"""
        response = await self._client._request("GET", "/models")
        return ModelList(**response)

    async def retrieve(self, model_id: str) -> Model:
        """Get details about a specific model (async)"""
        response = await self._client._request("GET", f"/models/{model_id}")
        return Model(**response)

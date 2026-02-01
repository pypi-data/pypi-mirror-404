"""
Cloud API client for making requests to the Moss cloud service.
"""

import os
from typing import Any, Dict, Optional, TypeVar

import httpx
from moss_core import CLOUD_API_BASE_URL as DEFAULT_CLOUD_API_BASE_URL

T = TypeVar("T")


def get_cloud_api_base_url() -> str:
    """Get the cloud API base URL, allowing environment variable override."""
    return os.getenv("MOSS_CLOUD_API_BASE_URL", DEFAULT_CLOUD_API_BASE_URL)


def get_cloud_query_url() -> str:
    """Get the cloud query URL, allowing environment variable override."""
    # Check for explicit query URL override first
    query_url = os.getenv("MOSS_CLOUD_QUERY_URL")
    if query_url:
        return query_url
    # Otherwise derive from base URL by replacing /manage with /query
    return get_cloud_api_base_url().replace("/manage", "/query")


class CloudApiClient:
    """
    Cloud API client for making requests to the Moss cloud service.
    """

    def __init__(self, project_id: str, project_key: str) -> None:
        """
        Initialize the cloud API client.

        Args:
            project_id: The project ID for authentication
            project_key: The project key for authentication
        """
        self.project_id = project_id
        self.project_key = project_key

    async def make_request(
        self,
        action: str,
        additional_data: Optional[Dict[str, Any]] = None,
        timeout: float = 600.0,
    ) -> Any:
        """
        Makes a POST request to the cloud API.

        Args:
            action: The action to perform
            additional_data: Additional data to include in the request
            timeout: Request timeout in seconds

        Returns:
            The response data from the API

        Raises:
            Exception: If the request fails or returns an error
        """
        request_body = {
            "action": action,
            "projectId": self.project_id,
        }

        if additional_data:
            request_body.update(additional_data)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    get_cloud_api_base_url(),
                    headers={
                        "Content-Type": "application/json",
                        "X-Service-Version": "v1",
                        "X-Project-Key": self.project_key,
                    },
                    json=request_body,
                )

                if not response.is_success:
                    raise Exception(f"HTTP error! status: {response.status_code}")

                data = response.json()
                return data

        except httpx.RequestError as error:
            raise Exception(f"Cloud API request failed: {str(error)}")
        except Exception as error:
            raise Exception(f"Cloud API request failed: {str(error)}")

    async def make_query_request(
        self,
        index_name: str,
        query: str,
        top_k: int = 10,
        query_embedding: Optional[list[float]] = None,
        timeout: float = 60.0,
    ) -> Any:
        """
        Makes a POST request to the cloud query endpoint.
        Used as fallback when index is not loaded locally.

        Args:
            index_name: Name of the index to query
            query: The search query text
            top_k: Number of results to return (default: 10, max: 50)
            query_embedding: Optional pre-computed query embedding for custom embeddings
            timeout: Request timeout in seconds

        Returns:
            The search results from the cloud API

        Raises:
            Exception: If the request fails or returns an error
        """
        cloud_query_url = get_cloud_query_url()
        request_body: Dict[str, Any] = {
            "query": query,
            "indexName": index_name,
            "projectId": self.project_id,
            "projectKey": self.project_key,
            "topK": top_k,
        }

        # Include query embedding if provided
        if query_embedding is not None:
            request_body["queryEmbedding"] = query_embedding

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    cloud_query_url,
                    headers={
                        "Content-Type": "application/json",
                    },
                    json=request_body,
                )

                if not response.is_success:
                    raise Exception(f"HTTP error! status: {response.status_code}")

                return response.json()

        except httpx.RequestError as error:
            raise Exception(f"Cloud query request failed: {str(error)}")
        except Exception as error:
            raise Exception(f"Cloud query request failed: {str(error)}")

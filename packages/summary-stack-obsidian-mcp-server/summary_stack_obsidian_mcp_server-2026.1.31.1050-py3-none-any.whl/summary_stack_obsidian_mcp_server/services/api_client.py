"""API client for consuming Summary Stack API SSE streams."""

import json
import logging
from typing import Any

import httpx

from summary_stack_obsidian_mcp_server.models import ObsidianManifestResult


logger = logging.getLogger(__name__)


class SummaryStackAPIError(Exception):
    """Error from Summary Stack API."""

    def __init__(self, message: str, event_type: str | None = None, metadata: dict[str, Any] | None = None):
        super().__init__(message)
        self.event_type = event_type
        self.metadata = metadata or {}


class SummaryStackAPIClient:
    """Client for consuming Summary Stack API SSE streams."""

    def __init__(self, api_url: str, api_key: str):
        """Initialize the API client.

        Args:
            api_url: Base URL of the Summary Stack API
            api_key: API key for authentication
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key

    async def create_obsidian_manifest(self, url: str) -> ObsidianManifestResult:
        """Stream SSE from API and return final ObsidianManifestResult.

        Args:
            url: URL to process into a summary stack

        Returns:
            ObsidianManifestResult with all data needed for vault writing

        Raises:
            SummaryStackAPIError: If API returns an error
            httpx.HTTPError: If request fails
        """
        async with (
            httpx.AsyncClient() as client,
            client.stream(
                "POST",
                f"{self.api_url}/api/v1/stacks",
                data={"uri": url, "connector": "obsidian"},
                headers={
                    "X-API-Key": self.api_key,
                    "Accept": "text/event-stream",
                },
                timeout=300.0,  # 5 minute timeout for long processing
            ) as response,
        ):
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue

                try:
                    event = json.loads(line[6:])
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse SSE event: {line}")
                    continue

                event_type = event.get("type", "")

                # Check for final success event
                if event_type == "obsidian_manifest_complete":
                    data = event.get("data", {})
                    return ObsidianManifestResult.model_validate(data)

                # Check for error events
                if event_type in ("obsidian_note_error", "processing_error"):
                    error_msg = event.get("data", {}).get("error", "Unknown error")
                    raise SummaryStackAPIError(
                        message=error_msg,
                        event_type=event_type,
                        metadata=event.get("data"),
                    )

                # Check for quota exceeded (different structure)
                if event_type == "quota_exceeded":
                    metadata = event.get("metadata", {})
                    used = metadata.get("used", "?")
                    limit = metadata.get("limit", "?")
                    resets_at = metadata.get("resets_at", "unknown")
                    error_msg = f"Quota exceeded: {used}/{limit} stacks used. Resets at {resets_at}"
                    logger.warning(f"Quota exceeded for request: {error_msg}")
                    raise SummaryStackAPIError(
                        message=error_msg,
                        event_type=event_type,
                        metadata=metadata,
                    )

        # If we get here, stream ended without a complete event
        raise SummaryStackAPIError("Stream ended without manifest_complete event")

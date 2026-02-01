"""Databricks Genie API client."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from .models import GenieSpace, SerializedSpace, SpaceDefinition


class GenieAPIError(Exception):
    """Exception raised for Genie API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class GenieClient:
    """Client for Databricks Genie Management API.

    API Reference: https://docs.databricks.com/api/workspace/genie
    """

    def __init__(
        self,
        host: str | None = None,
        token: str | None = None,
        timeout: float = 60.0,
    ):
        """Initialize the Genie API client.

        Args:
            host: Databricks workspace host URL. Falls back to DATABRICKS_HOST env var.
            token: Databricks access token. Falls back to DATABRICKS_TOKEN env var.
            timeout: Request timeout in seconds.
        """
        self.host = (host or os.environ.get("DATABRICKS_HOST", "")).rstrip("/")
        self.token = token or os.environ.get("DATABRICKS_TOKEN", "")

        if not self.host:
            raise ValueError(
                "Databricks host is required. Set DATABRICKS_HOST or pass host parameter."
            )
        if not self.token:
            raise ValueError(
                "Databricks token is required. Set DATABRICKS_TOKEN or pass token parameter."
            )

        self._client = httpx.Client(
            base_url=f"{self.host}/api/2.0",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and raise errors if needed."""
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw": response.text}

        if response.status_code >= 400:
            error_message = data.get("message", data.get("error", str(data)))
            raise GenieAPIError(
                f"API error: {error_message}",
                status_code=response.status_code,
                response=data,
            )

        return data

    def get_space(self, space_id: str, include_serialized: bool = True) -> GenieSpace:
        """Get a Genie space by ID.

        Args:
            space_id: The ID of the space to retrieve.
            include_serialized: Whether to include the serialized space configuration.

        Returns:
            GenieSpace object with space details.
        """
        params = {}
        if include_serialized:
            params["include_serialized_space"] = "true"

        response = self._client.get(f"/genie/spaces/{space_id}", params=params)
        data = self._handle_response(response)

        return GenieSpace(**data)

    def create_space(
        self,
        title: str,
        warehouse_id: str,
        serialized_space: SerializedSpace | dict | None = None,
        description: str | None = None,
    ) -> GenieSpace:
        """Create a new Genie space.

        Args:
            title: Title of the space.
            warehouse_id: ID of the SQL warehouse to use.
            serialized_space: Space configuration (tables, joins, instructions, etc.).
            description: Optional description.

        Returns:
            Created GenieSpace object with space_id.
        """
        payload: dict[str, Any] = {
            "title": title,
            "warehouse_id": warehouse_id,
        }

        if description:
            payload["description"] = description

        if serialized_space:
            if isinstance(serialized_space, SerializedSpace):
                # Exclude None values to match API expectations
                payload["serialized_space"] = json.dumps(
                    serialized_space.model_dump(exclude_none=True, mode="json")
                )
            else:
                payload["serialized_space"] = json.dumps(serialized_space)

        response = self._client.post("/genie/spaces", json=payload)
        data = self._handle_response(response)

        return GenieSpace(**data)

    def update_space(
        self,
        space_id: str,
        title: str | None = None,
        warehouse_id: str | None = None,
        serialized_space: SerializedSpace | dict | None = None,
        description: str | None = None,
    ) -> GenieSpace:
        """Update an existing Genie space.

        Args:
            space_id: ID of the space to update.
            title: New title (optional).
            warehouse_id: New warehouse ID (optional).
            serialized_space: New space configuration (optional).
            description: New description (optional).

        Returns:
            Updated GenieSpace object.
        """
        payload: dict[str, Any] = {}

        if title is not None:
            payload["title"] = title
        if warehouse_id is not None:
            payload["warehouse_id"] = warehouse_id
        if description is not None:
            payload["description"] = description

        if serialized_space is not None:
            if isinstance(serialized_space, SerializedSpace):
                # Exclude None values to match API expectations
                payload["serialized_space"] = json.dumps(
                    serialized_space.model_dump(exclude_none=True, mode="json")
                )
            else:
                payload["serialized_space"] = json.dumps(serialized_space)

        response = self._client.patch(f"/genie/spaces/{space_id}", json=payload)
        data = self._handle_response(response)

        return GenieSpace(**data)

    def delete_space(self, space_id: str) -> None:
        """Delete a Genie space.

        Args:
            space_id: ID of the space to delete.
        """
        response = self._client.delete(f"/genie/spaces/{space_id}")
        self._handle_response(response)

    def list_spaces(
        self, page_token: str | None = None, page_size: int = 100
    ) -> tuple[list[GenieSpace], str | None]:
        """List all Genie spaces in the workspace.

        Args:
            page_token: Token for pagination.
            page_size: Number of results per page.

        Returns:
            Tuple of (list of spaces, next page token or None).
        """
        params: dict[str, Any] = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token

        response = self._client.get("/genie/spaces", params=params)
        data = self._handle_response(response)

        spaces = [GenieSpace(**s) for s in data.get("spaces", [])]
        next_token = data.get("next_page_token")

        return spaces, next_token

    def push_space(
        self,
        definition: SpaceDefinition,
        space_id: str | None = None,
        warehouse_id: str | None = None,
    ) -> GenieSpace:
        """Push a space definition - creates if space_id is None, updates otherwise.

        Args:
            definition: The space definition to push.
            space_id: Existing space ID to update, or None to create new.
            warehouse_id: Override warehouse ID from definition.

        Returns:
            Created or updated GenieSpace object.
        """
        wh_id = warehouse_id or definition.warehouse_id
        if not wh_id:
            raise ValueError("warehouse_id is required either in definition or as parameter")

        serialized = definition.to_serialized_space()

        if space_id:
            return self.update_space(
                space_id=space_id,
                title=definition.title,
                warehouse_id=wh_id,
                serialized_space=serialized,
                description=definition.description,
            )
        else:
            return self.create_space(
                title=definition.title,
                warehouse_id=wh_id,
                serialized_space=serialized,
                description=definition.description,
            )

    def start_conversation(self, space_id: str) -> str:
        """Start a new conversation with a Genie space.

        Args:
            space_id: ID of the space.

        Returns:
            Conversation ID.
        """
        response = self._client.post(f"/genie/spaces/{space_id}/conversations")
        data = self._handle_response(response)
        return data["conversation_id"]

    def send_message(
        self,
        space_id: str,
        conversation_id: str,
        content: str,
    ) -> dict[str, Any]:
        """Send a message to a Genie conversation.

        Args:
            space_id: ID of the space.
            conversation_id: ID of the conversation.
            content: Message content (natural language query).

        Returns:
            Message response with query results.
        """
        payload = {"content": content}
        response = self._client.post(
            f"/genie/spaces/{space_id}/conversations/{conversation_id}/messages",
            json=payload,
        )
        return self._handle_response(response)

    def get_message(
        self,
        space_id: str,
        conversation_id: str,
        message_id: str,
    ) -> dict[str, Any]:
        """Get a message from a Genie conversation.

        Args:
            space_id: ID of the space.
            conversation_id: ID of the conversation.
            message_id: ID of the message.

        Returns:
            Message details including SQL and results.
        """
        response = self._client.get(
            f"/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}"
        )
        return self._handle_response(response)

    def execute_query(
        self,
        space_id: str,
        conversation_id: str,
        message_id: str,
    ) -> dict[str, Any]:
        """Execute the SQL query from a message.

        Args:
            space_id: ID of the space.
            conversation_id: ID of the conversation.
            message_id: ID of the message containing the query.

        Returns:
            Query execution results.
        """
        response = self._client.post(
            f"/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/execute-query"
        )
        return self._handle_response(response)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> GenieClient:
        return self

    def __exit__(self, *args) -> None:
        self.close()

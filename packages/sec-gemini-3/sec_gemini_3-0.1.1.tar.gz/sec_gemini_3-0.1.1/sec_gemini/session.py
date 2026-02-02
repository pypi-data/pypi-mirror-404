from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable
import logging

from . import api_pb2
from . import constants
from .mcp import Mcp

logger = logging.getLogger("sec-gemini")


@dataclass
class Session:
    id: str
    status_int: int = api_pb2.JobStatus.PENDING

    _name: str = ""
    _client: Any = field(default=None, repr=False)
    _status_callbacks: list[Callable] = field(default_factory=list, repr=False)

    def bind(self, client):
        self._client = client

    def add_status_callback(self, callback: Callable):
        """Add a callback to be called when the status changes."""
        self._status_callbacks.append(callback)

    def update_from_event(self, event_content: dict):
        """Updates the status of the session from streamed events."""
        if constants.SESSION_EVENT_STATUS in event_content:
            try:
                self.status_int = api_pb2.JobStatus.Value(
                    event_content[constants.SESSION_EVENT_STATUS].upper()
                )
                for callback in self._status_callbacks:
                    callback(self.id, self.status)
            except ValueError:
                pass

    @property
    def status(self) -> str:
        """String representation of the status"""
        return api_pb2.JobStatus.Name(self.status_int)

    @property
    def name(self) -> str:
        """String representation of the session name"""
        if not self._name:
            return "New Session"
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    async def set_confirmation_config(
        self, always_ask_for_tool_confirmation: bool
    ) -> bool:
        """Set the confirmation config for a session"""
        if self._client:
            return await self._client._set_confirmation_config(
                self.id, always_ask_for_tool_confirmation
            )
        return False

    async def set_mcps(self, mcps: list[str]) -> bool:
        """Set the MCPs for a session"""
        if self._client:
            return await self._client._set_mcps(self.id, mcps)
        return False

    async def list_mcps(self) -> list[Mcp]:
        """List all available MCPs"""
        if self._client:
            return await self._client._mcps(self.id)
        return []

    async def list_skills(self) -> list[Mcp]:
        """List all available skills"""
        if self._client:
            return await self._client._skills(self.id)
        return []

    async def prompt(self, text: str, meta: dict[str, str] | None = None):
        """Send a prompt to start a job"""
        if self._client:
            await self._client._send_prompt(self.id, text, meta=meta)
            # Set the session name with the first prompt.
            if self.name == "New Session":
                self.name = text[:20]

    async def cancel(self):
        """Cancel the session"""
        if self._client:
            await self._client._cancel_session(self.id)

    async def resume(self):
        """Resume the session"""
        if self._client:
            await self._client._resume_session(self.id)

    async def get_confirmation_info(self):
        """Get confirmation info for a session"""
        if self._client:
            return await self._client._get_tool_confirmation_request(self.id)
        return None

    async def send_tool_confirmation(self, action_id: str, confirmed: bool = True):
        """Confirm an action"""
        if self._client:
            await self._client._send_tool_confirmation(self.id, action_id, confirmed)

    async def stream_messages(self) -> AsyncIterator[dict]:
        """Stream messages from the server"""
        from google.protobuf.json_format import MessageToDict

        if self._client:
            async for msg in self._client._stream_messages(self.id):
                yield MessageToDict(
                    msg,
                    preserving_proto_field_name=True,
                    always_print_fields_with_no_presence=True,
                )

    async def pause(self):
        """Pause the session"""
        if self._client:
            await self._client._pause_session(self.id)

    async def delete(self):
        """Delete the session"""
        if self._client:
            return await self._client._delete_session(self.id)
        return False

    async def upload_file(self, file_path: str):
        """Upload a file to the session"""
        if self._client:
            await self._client._upload_file(self.id, file_path)

    async def list_files(self) -> list[api_pb2.FileInfo]:
        """List all uploaded files for a session."""
        if self._client:
            return await self._client._list_files(self.id)
        return []

    async def delete_file(self, filename: str) -> bool:
        """Delete a file from a session."""
        if self._client:
            return await self._client._delete_file(self.id, filename)
        return False

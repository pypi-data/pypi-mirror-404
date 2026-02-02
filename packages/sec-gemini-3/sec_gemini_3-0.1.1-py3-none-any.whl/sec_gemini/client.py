import uuid
import asyncio
from typing import Dict, List, Optional, AsyncIterator

from . import api_pb2, constants
import os
import grpc
import logging
from rich.logging import RichHandler

from .session import Session
from .connection import RpcClient
from .mcp import Mcp

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(markup=True)],
)
logger = logging.getLogger("secgemini")


class SecGemini:
    def __init__(
        self,
        api_key: str,
        host: str = constants.API_HUB_HOST,
    ):
        self._api_key = api_key
        self.rpc = RpcClient(host)
        self.rpc.add_message_handler(self._handle_server_message)

        self.available_mcps: List[Mcp] = []
        self._sessions: Dict[str, Session] = {}

    async def start(self):
        """Start the client, connect to server, and register"""
        await self.rpc.start()
        # Register
        await self._register()

    async def close(self):
        """Stop the client and close connections"""
        await self.rpc.close()

    async def _register(self):
        """Login to the API Hub"""
        register_msg = api_pb2.RegisterRequest(api_key=self._api_key)
        resp = await self.rpc.send_request(
            constants.MSG_REGISTER, register_msg, wait_for_response=True
        )
        if resp and resp.HasField(constants.SERVER_MSG_REGISTER_RESPONSE):
            if not resp.register_response.success:
                raise PermissionError(
                    f"Authentication failed: {resp.register_response.message}"
                )
            logger.info("Authenticated!")
        else:
            raise ConnectionError("Failed to register with API Hub")

    async def _handle_server_message(self, msg: api_pb2.ServerMessage):
        """Handle messages from the API hub."""
        if msg.HasField(constants.SERVER_MSG_SESSION_STATE_CHANGE):
            event = msg.session_state_change
            if event.session_id in self._sessions:
                session = self._sessions[event.session_id]
                try:
                    session.update_from_event(
                        {
                            constants.SESSION_EVENT_STATUS: api_pb2.JobStatus.Name(
                                event.status
                            )
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to handle session state change: {e}")

    async def _mcps(self, session_id: Optional[str] = None) -> List[Mcp]:
        """List all available MCPs"""
        req = api_pb2.ListMcpsRequest()
        resp = await self.rpc.send_request(
            constants.MSG_LIST_MCPS, req, wait_for_response=True, session_id=session_id
        )
        if resp and resp.HasField(constants.SERVER_MSG_LIST_MCPS_RESPONSE):
            result = [Mcp(m) for m in resp.list_mcps_response.mcps]
            self.available_mcps = result
            return result
        return []

    async def _skills(self, session_id: Optional[str] = None) -> List[Mcp]:
        """List all available skills"""
        req = api_pb2.ListSkillsRequest()
        resp = await self.rpc.send_request(
            constants.MSG_LIST_SKILLS,
            req,
            wait_for_response=True,
            session_id=session_id,
        )
        if resp and resp.HasField(constants.SERVER_MSG_LIST_SKILLS_RESPONSE):
            result = [Mcp(m) for m in resp.list_skills_response.mcps]
            self.available_mcps = result
            return result
        return []

    async def _upload_file(
        self,
        session_id: str,
        file_path: str,
        content_type: str = "application/octet-stream",
    ) -> None:
        """Upload a file to the API Hub.

        Args:
            session_id: The session ID to associate the file with.
            file_path: Path to the file to upload.
            content_type: MIME type of the file.


        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = os.path.basename(file_path)

        async def upload_iterator():
            # 1. Send metadata
            yield api_pb2.UploadFileRequest(
                metadata=api_pb2.FileMetadata(
                    session_id=session_id,
                    filename=filename,
                    content_type=content_type,
                )
            )
            # 2. Send chunks
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    yield api_pb2.UploadFileRequest(chunk=chunk)

        try:
            assert self.rpc.stub is not None
            response = await self.rpc.stub.UploadFile(upload_iterator())
            if not response.success:
                raise Exception(response.error_message)
            return

        except grpc.RpcError as e:
            logger.error(f"gRPC Upload failed: {e}")
            raise

    async def _list_files(self, session_id: str) -> List[api_pb2.FileInfo]:
        """List all uploaded files for a session."""
        resp = await self.rpc.send_request(
            constants.MSG_LIST_FILES,
            api_pb2.ListFilesRequest(),
            wait_for_response=True,
            session_id=session_id,
        )
        if resp and resp.HasField(constants.SERVER_MSG_LIST_FILES_RESPONSE):
            if resp.list_files_response.success:
                return list(resp.list_files_response.files)
        return []

    async def _delete_file(self, session_id: str, filename: str) -> bool:
        """Delete a file from a session.

        Args:
            session_id: The session ID.
            filename: The name of the file to delete.

        Returns:
            True if deletion was successful, False otherwise.
        """
        req = api_pb2.DeleteFileRequest(session_id=session_id, filename=filename)
        resp = await self.rpc.send_request(
            constants.MSG_DELETE_FILE,
            req,
            wait_for_response=True,
            session_id=session_id,
        )
        if resp and resp.HasField(constants.SERVER_MSG_DELETE_FILE_RESPONSE):
            if not resp.delete_file_response.success:
                logger.error(
                    f"Failed to delete file: {resp.delete_file_response.error_message}"
                )
                return False
            return True
        return False

    async def sessions(self) -> List[Session]:
        """List all sessions"""
        resp = await self.rpc.send_request(
            constants.MSG_LIST_SESSIONS,
            api_pb2.ListSessionsRequest(),
            wait_for_response=True,
        )
        if resp and resp.HasField(constants.SERVER_MSG_LIST_SESSIONS_RESPONSE):
            result = []
            for s in resp.list_sessions_response.sessions:
                sess = Session(
                    id=s.session_id,
                    status_int=s.status,
                )
                sess.bind(self)
                result.append(sess)
                self._sessions[s.session_id] = sess
            return result
        return list(self._sessions.values())

    async def create_session(self) -> Session:
        """Create a new session"""
        create_msg = api_pb2.CreateSessionRequest()
        resp = await self.rpc.send_request(
            constants.MSG_CREATE_SESSION, create_msg, wait_for_response=True
        )
        if resp and resp.HasField(constants.SERVER_MSG_CREATE_SESSION_RESPONSE):
            if not resp.create_session_response.success:
                raise RuntimeError("Failed to create session: Server returned failure")

            sid = resp.create_session_response.session_id
            sess = Session(id=sid)
            sess.bind(self)
            self._sessions[sid] = sess
            return sess
        else:
            raise RuntimeError("Failed to create session: No valid response")

    async def _delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        req = api_pb2.DeleteSessionRequest()
        resp = await self.rpc.send_request(
            constants.MSG_DELETE_SESSION,
            req,
            wait_for_response=True,
            session_id=session_id,
        )
        if resp and resp.HasField(constants.SERVER_MSG_DELETE_SESSION_RESPONSE):
            if not resp.delete_session_response.success:
                logger.error("Failed to delete session")
                return False

            if session_id in self._sessions:
                del self._sessions[session_id]
            return True
        return False

    async def _set_mcps(self, session_id: str, mcps: List[str]) -> bool:
        """Set the MCPs for a session"""
        req = api_pb2.SetMcpsRequest(mcp_servers=mcps)
        resp = await self.rpc.send_request(
            constants.MSG_SET_MCPS,
            req,
            wait_for_response=True,
            session_id=session_id,
        )
        if resp and resp.HasField(constants.SERVER_MSG_SET_MCPS_RESPONSE):
            return resp.set_mcps_response.success
        return False

    async def _set_confirmation_config(
        self, session_id: str, always_ask_for_tool_confirmation: bool
    ) -> bool:
        """Set the confirmation config for a session"""
        req = api_pb2.SetConfirmationConfigRequest(
            always_ask_for_tool_confirmation=always_ask_for_tool_confirmation
        )
        resp = await self.rpc.send_request(
            constants.MSG_SET_CONFIRMATION_CONFIG,
            req,
            wait_for_response=True,
            session_id=session_id,
        )
        if resp and resp.HasField(
            constants.SERVER_MSG_SET_CONFIRMATION_CONFIG_RESPONSE
        ):
            return resp.set_confirmation_config_response.success
        return False

    async def _send_prompt(
        self, session_id: str, prompt: str, meta: dict[str, str] | None = None
    ):
        """Send a prompt to start a job in a session"""
        prompt_msg = api_pb2.PromptRequest(prompt=prompt, meta=meta)
        await self.rpc.send_request(
            constants.MSG_PROMPT,
            prompt_msg,
            wait_for_response=True,
            session_id=session_id,
        )

    async def _resume_session(self, session_id: str):
        """Resume a session"""
        req = api_pb2.ResumeSessionRequest()
        await self.rpc.send_request(
            constants.MSG_RESUME_SESSION,
            req,
            wait_for_response=True,
            session_id=session_id,
        )

    async def _pause_session(self, session_id: str):
        """Pause a session"""
        req = api_pb2.PauseSessionRequest()
        await self.rpc.send_request(
            constants.MSG_PAUSE_SESSION,
            req,
            wait_for_response=True,
            session_id=session_id,
        )

    async def _get_tool_confirmation_request(self, session_id: str):
        """Get confirmation info for a session"""
        req = api_pb2.GetConfirmationInfoRequest()
        resp = await self.rpc.send_request(
            constants.MSG_GET_CONFIRMATION_INFO,
            req,
            wait_for_response=True,
            session_id=session_id,
        )

        if resp and resp.HasField(constants.SERVER_MSG_GET_CONFIRMATION_INFO_RESPONSE):
            return resp.get_confirmation_info_response
        return None

    async def _send_tool_confirmation(
        self, session_id: str, confirmation_id: str, confirmation_response: bool = True
    ):
        """Send a confirmation for a tool action."""
        req = api_pb2.ConfirmActionRequest(
            confirmation_id=confirmation_id, confirmation_response=confirmation_response
        )
        await self.rpc.send_request(
            constants.MSG_CONFIRM_ACTION,
            req,
            wait_for_response=True,
            session_id=session_id,
        )

    async def _cancel_session(self, session_id: str):
        """Cancel a session"""
        req = api_pb2.CancelSessionRequest()
        await self.rpc.send_request(
            constants.MSG_CANCEL_SESSION,
            req,
            wait_for_response=True,
            session_id=session_id,
        )

    async def _stream_messages(self, session_id: str) -> AsyncIterator[api_pb2.Message]:
        """Streaming messages via callback"""
        req_id = str(uuid.uuid4())
        q = asyncio.Queue()
        self.rpc.register_streaming_queue(req_id, q)

        req = api_pb2.StreamMessagesRequest()

        await self.rpc.send_request(
            constants.MSG_STREAM_MESSAGES,
            req,
            wait_for_response=False,
            session_id=session_id,
            req_id=req_id,
        )

        try:
            while True:
                server_msg = await q.get()
                if server_msg.HasField(constants.SERVER_MSG_MESSAGE):
                    yield server_msg.message
                # If prismy is done, stop streaming
                if server_msg.HasField(
                    constants.SERVER_MSG_SESSION_STATE_CHANGE
                ) and server_msg.session_state_change.status in [
                    api_pb2.JobStatus.COMPLETED,
                    api_pb2.JobStatus.FAILED,
                    api_pb2.JobStatus.CANCELED,
                    api_pb2.JobStatus.MAX_ATTEMPTS_EXCEEDED,
                    api_pb2.JobStatus.WAITING_FOR_TOOL_CONFIRMATION,
                    api_pb2.JobStatus.WAITING_FOR_CLARIFICATION,
                ]:
                    break
        finally:
            self.rpc.unregister_streaming_queue(req_id)

            # Send Stop
            stop_req = api_pb2.StopStreamMessagesRequest()
            await self.rpc.send_request(
                constants.MSG_STOP_STREAM_MESSAGES,
                stop_req,
                session_id=session_id,
                wait_for_response=False,
            )

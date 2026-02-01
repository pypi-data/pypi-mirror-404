from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class JobStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NOT_INITIALIZED: _ClassVar[JobStatus]
    PENDING: _ClassVar[JobStatus]
    RUNNING: _ClassVar[JobStatus]
    PAUSED: _ClassVar[JobStatus]
    CANCELED: _ClassVar[JobStatus]
    COMPLETED: _ClassVar[JobStatus]
    FAILED: _ClassVar[JobStatus]
    WAITING_FOR_TOOL_CONFIRMATION: _ClassVar[JobStatus]
    WAITING_FOR_CLARIFICATION: _ClassVar[JobStatus]
    MAX_ATTEMPTS_EXCEEDED: _ClassVar[JobStatus]

class McpStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MCP_UNKNOWN: _ClassVar[McpStatus]
    MCP_RUNNING: _ClassVar[McpStatus]
    MCP_UNREACHABLE: _ClassVar[McpStatus]

class SourceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SOURCE_TYPE_UNSPECIFIED: _ClassVar[SourceType]
    SOURCE_TYPE_USER: _ClassVar[SourceType]
    SOURCE_TYPE_AGENT: _ClassVar[SourceType]
    SOURCE_TYPE_SYSTEM: _ClassVar[SourceType]

class MessageType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MESSAGE_TYPE_UNSPECIFIED: _ClassVar[MessageType]
    MESSAGE_TYPE_USER_QUERY: _ClassVar[MessageType]
    MESSAGE_TYPE_RESPONSE: _ClassVar[MessageType]
    MESSAGE_TYPE_THOUGHT: _ClassVar[MessageType]
    MESSAGE_TYPE_TOOL_CALL: _ClassVar[MessageType]
    MESSAGE_TYPE_TOOL_RESULT: _ClassVar[MessageType]
    MESSAGE_TYPE_ERROR: _ClassVar[MessageType]
    MESSAGE_TYPE_INFO: _ClassVar[MessageType]
    MESSAGE_TYPE_DEBUG: _ClassVar[MessageType]
    MESSAGE_TYPE_AGENT_IS_DONE: _ClassVar[MessageType]
    MESSAGE_TYPE_USER_QUERY_COMPLETED: _ClassVar[MessageType]
    MESSAGE_TYPE_TOOL_CONFIRMATION_REQUEST: _ClassVar[MessageType]
    MESSAGE_TYPE_TOOL_CONFIRMATION_RESPONSE: _ClassVar[MessageType]
    MESSAGE_TYPE_CLARIFICATION_REQUEST: _ClassVar[MessageType]
    MESSAGE_TYPE_CLARIFICATION_RESPONSE: _ClassVar[MessageType]

class RenderType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RENDER_TYPE_UNSPECIFIED: _ClassVar[RenderType]
    RENDER_TYPE_MARKDOWN: _ClassVar[RenderType]
    RENDER_TYPE_TEXT: _ClassVar[RenderType]
    RENDER_TYPE_HTML: _ClassVar[RenderType]
    RENDER_TYPE_GRAPH: _ClassVar[RenderType]
    RENDER_TYPE_TABLE: _ClassVar[RenderType]
    RENDER_TYPE_TIMELINE: _ClassVar[RenderType]
    RENDER_TYPE_JSON: _ClassVar[RenderType]

class MimeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MIME_TYPE_UNSPECIFIED: _ClassVar[MimeType]
    MIME_TYPE_TEXT: _ClassVar[MimeType]
    MIME_TYPE_MARKDOWN: _ClassVar[MimeType]
    MIME_TYPE_SERIALIZED_JSON: _ClassVar[MimeType]
    MIME_TYPE_BINARY: _ClassVar[MimeType]
    MIME_TYPE_JPEG: _ClassVar[MimeType]
    MIME_TYPE_PNG: _ClassVar[MimeType]
    MIME_TYPE_TIFF: _ClassVar[MimeType]
    MIME_TYPE_GIF: _ClassVar[MimeType]
    MIME_TYPE_SVG: _ClassVar[MimeType]
    MIME_TYPE_WEBP: _ClassVar[MimeType]
    MIME_TYPE_AVIF: _ClassVar[MimeType]
    MIME_TYPE_WAV: _ClassVar[MimeType]
    MIME_TYPE_MP3: _ClassVar[MimeType]
    MIME_TYPE_OGG: _ClassVar[MimeType]
    MIME_TYPE_WEBM: _ClassVar[MimeType]
    MIME_TYPE_MP4: _ClassVar[MimeType]
    MIME_TYPE_C: _ClassVar[MimeType]
    MIME_TYPE_CPP: _ClassVar[MimeType]
    MIME_TYPE_JAVA: _ClassVar[MimeType]
    MIME_TYPE_RUST: _ClassVar[MimeType]
    MIME_TYPE_GOLANG: _ClassVar[MimeType]
    MIME_TYPE_PYTHON: _ClassVar[MimeType]
    MIME_TYPE_PHP: _ClassVar[MimeType]
    MIME_TYPE_PERL: _ClassVar[MimeType]
    MIME_TYPE_RUBY: _ClassVar[MimeType]
    MIME_TYPE_SWIFT: _ClassVar[MimeType]
    MIME_TYPE_KOTLIN: _ClassVar[MimeType]
    MIME_TYPE_SCALA: _ClassVar[MimeType]
    MIME_TYPE_JAVASCRIPT: _ClassVar[MimeType]
    MIME_TYPE_TYPESCRIPT: _ClassVar[MimeType]
    MIME_TYPE_HTML: _ClassVar[MimeType]
    MIME_TYPE_CSS: _ClassVar[MimeType]
    MIME_TYPE_CSV: _ClassVar[MimeType]
    MIME_TYPE_XML: _ClassVar[MimeType]
    MIME_TYPE_YAML: _ClassVar[MimeType]
    MIME_TYPE_TOML: _ClassVar[MimeType]
    MIME_TYPE_SQL: _ClassVar[MimeType]
    MIME_TYPE_JSON: _ClassVar[MimeType]
    MIME_TYPE_JSONL: _ClassVar[MimeType]
    MIME_TYPE_PDF: _ClassVar[MimeType]
    MIME_TYPE_DOCX: _ClassVar[MimeType]
    MIME_TYPE_XLSX: _ClassVar[MimeType]
    MIME_TYPE_PPTX: _ClassVar[MimeType]
    MIME_TYPE_DOC: _ClassVar[MimeType]
    MIME_TYPE_XLS: _ClassVar[MimeType]
    MIME_TYPE_PPT: _ClassVar[MimeType]
    MIME_TYPE_RTF: _ClassVar[MimeType]
    MIME_TYPE_ODT: _ClassVar[MimeType]
NOT_INITIALIZED: JobStatus
PENDING: JobStatus
RUNNING: JobStatus
PAUSED: JobStatus
CANCELED: JobStatus
COMPLETED: JobStatus
FAILED: JobStatus
WAITING_FOR_TOOL_CONFIRMATION: JobStatus
WAITING_FOR_CLARIFICATION: JobStatus
MAX_ATTEMPTS_EXCEEDED: JobStatus
MCP_UNKNOWN: McpStatus
MCP_RUNNING: McpStatus
MCP_UNREACHABLE: McpStatus
SOURCE_TYPE_UNSPECIFIED: SourceType
SOURCE_TYPE_USER: SourceType
SOURCE_TYPE_AGENT: SourceType
SOURCE_TYPE_SYSTEM: SourceType
MESSAGE_TYPE_UNSPECIFIED: MessageType
MESSAGE_TYPE_USER_QUERY: MessageType
MESSAGE_TYPE_RESPONSE: MessageType
MESSAGE_TYPE_THOUGHT: MessageType
MESSAGE_TYPE_TOOL_CALL: MessageType
MESSAGE_TYPE_TOOL_RESULT: MessageType
MESSAGE_TYPE_ERROR: MessageType
MESSAGE_TYPE_INFO: MessageType
MESSAGE_TYPE_DEBUG: MessageType
MESSAGE_TYPE_AGENT_IS_DONE: MessageType
MESSAGE_TYPE_USER_QUERY_COMPLETED: MessageType
MESSAGE_TYPE_TOOL_CONFIRMATION_REQUEST: MessageType
MESSAGE_TYPE_TOOL_CONFIRMATION_RESPONSE: MessageType
MESSAGE_TYPE_CLARIFICATION_REQUEST: MessageType
MESSAGE_TYPE_CLARIFICATION_RESPONSE: MessageType
RENDER_TYPE_UNSPECIFIED: RenderType
RENDER_TYPE_MARKDOWN: RenderType
RENDER_TYPE_TEXT: RenderType
RENDER_TYPE_HTML: RenderType
RENDER_TYPE_GRAPH: RenderType
RENDER_TYPE_TABLE: RenderType
RENDER_TYPE_TIMELINE: RenderType
RENDER_TYPE_JSON: RenderType
MIME_TYPE_UNSPECIFIED: MimeType
MIME_TYPE_TEXT: MimeType
MIME_TYPE_MARKDOWN: MimeType
MIME_TYPE_SERIALIZED_JSON: MimeType
MIME_TYPE_BINARY: MimeType
MIME_TYPE_JPEG: MimeType
MIME_TYPE_PNG: MimeType
MIME_TYPE_TIFF: MimeType
MIME_TYPE_GIF: MimeType
MIME_TYPE_SVG: MimeType
MIME_TYPE_WEBP: MimeType
MIME_TYPE_AVIF: MimeType
MIME_TYPE_WAV: MimeType
MIME_TYPE_MP3: MimeType
MIME_TYPE_OGG: MimeType
MIME_TYPE_WEBM: MimeType
MIME_TYPE_MP4: MimeType
MIME_TYPE_C: MimeType
MIME_TYPE_CPP: MimeType
MIME_TYPE_JAVA: MimeType
MIME_TYPE_RUST: MimeType
MIME_TYPE_GOLANG: MimeType
MIME_TYPE_PYTHON: MimeType
MIME_TYPE_PHP: MimeType
MIME_TYPE_PERL: MimeType
MIME_TYPE_RUBY: MimeType
MIME_TYPE_SWIFT: MimeType
MIME_TYPE_KOTLIN: MimeType
MIME_TYPE_SCALA: MimeType
MIME_TYPE_JAVASCRIPT: MimeType
MIME_TYPE_TYPESCRIPT: MimeType
MIME_TYPE_HTML: MimeType
MIME_TYPE_CSS: MimeType
MIME_TYPE_CSV: MimeType
MIME_TYPE_XML: MimeType
MIME_TYPE_YAML: MimeType
MIME_TYPE_TOML: MimeType
MIME_TYPE_SQL: MimeType
MIME_TYPE_JSON: MimeType
MIME_TYPE_JSONL: MimeType
MIME_TYPE_PDF: MimeType
MIME_TYPE_DOCX: MimeType
MIME_TYPE_XLSX: MimeType
MIME_TYPE_PPTX: MimeType
MIME_TYPE_DOC: MimeType
MIME_TYPE_XLS: MimeType
MIME_TYPE_PPT: MimeType
MIME_TYPE_RTF: MimeType
MIME_TYPE_ODT: MimeType

class McpTool(_message.Message):
    __slots__ = ("name", "description")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class McpSkill(_message.Message):
    __slots__ = ("name", "description")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class McpInfo(_message.Message):
    __slots__ = ("name", "uri", "status", "tools", "skills")
    NAME_FIELD_NUMBER: _ClassVar[int]
    URI_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TOOLS_FIELD_NUMBER: _ClassVar[int]
    SKILLS_FIELD_NUMBER: _ClassVar[int]
    name: str
    uri: str
    status: McpStatus
    tools: _containers.RepeatedCompositeFieldContainer[McpTool]
    skills: _containers.RepeatedCompositeFieldContainer[McpSkill]
    def __init__(self, name: _Optional[str] = ..., uri: _Optional[str] = ..., status: _Optional[_Union[McpStatus, str]] = ..., tools: _Optional[_Iterable[_Union[McpTool, _Mapping]]] = ..., skills: _Optional[_Iterable[_Union[McpSkill, _Mapping]]] = ...) -> None: ...

class SessionInfo(_message.Message):
    __slots__ = ("session_id", "status")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    status: JobStatus
    def __init__(self, session_id: _Optional[str] = ..., status: _Optional[_Union[JobStatus, str]] = ...) -> None: ...

class ToolCallConfirmationInfo(_message.Message):
    __slots__ = ("id", "tool_name", "tool_args", "message")
    ID_FIELD_NUMBER: _ClassVar[int]
    TOOL_NAME_FIELD_NUMBER: _ClassVar[int]
    TOOL_ARGS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    id: str
    tool_name: str
    tool_args: _struct_pb2.Struct
    message: str
    def __init__(self, id: _Optional[str] = ..., tool_name: _Optional[str] = ..., tool_args: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., message: _Optional[str] = ...) -> None: ...

class Error(_message.Message):
    __slots__ = ("code", "message")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    code: str
    message: str
    def __init__(self, code: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class Message(_message.Message):
    __slots__ = ("id", "timestamp", "source_type", "source", "title", "content", "message_type", "mime_type", "render_type", "snapshot_id")
    ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    MIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    RENDER_TYPE_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    timestamp: float
    source_type: SourceType
    source: str
    title: str
    content: str
    message_type: MessageType
    mime_type: MimeType
    render_type: RenderType
    snapshot_id: str
    def __init__(self, id: _Optional[str] = ..., timestamp: _Optional[float] = ..., source_type: _Optional[_Union[SourceType, str]] = ..., source: _Optional[str] = ..., title: _Optional[str] = ..., content: _Optional[str] = ..., message_type: _Optional[_Union[MessageType, str]] = ..., mime_type: _Optional[_Union[MimeType, str]] = ..., render_type: _Optional[_Union[RenderType, str]] = ..., snapshot_id: _Optional[str] = ...) -> None: ...

class ClientMessage(_message.Message):
    __slots__ = ("req_id", "session_id", "register", "create_session_request", "delete_session_request", "pause_session_request", "resume_session_request", "list_mcps_request", "list_skills_request", "list_sessions_request", "prompt_request", "confirm_action_request", "cancel_session_request", "stream_messages_request", "stop_stream_messages_request", "list_files_request", "delete_file_request", "set_mcps_request", "set_confirmation_config_request", "get_confirmation_info_request")
    REQ_ID_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    REGISTER_FIELD_NUMBER: _ClassVar[int]
    CREATE_SESSION_REQUEST_FIELD_NUMBER: _ClassVar[int]
    DELETE_SESSION_REQUEST_FIELD_NUMBER: _ClassVar[int]
    PAUSE_SESSION_REQUEST_FIELD_NUMBER: _ClassVar[int]
    RESUME_SESSION_REQUEST_FIELD_NUMBER: _ClassVar[int]
    LIST_MCPS_REQUEST_FIELD_NUMBER: _ClassVar[int]
    LIST_SKILLS_REQUEST_FIELD_NUMBER: _ClassVar[int]
    LIST_SESSIONS_REQUEST_FIELD_NUMBER: _ClassVar[int]
    PROMPT_REQUEST_FIELD_NUMBER: _ClassVar[int]
    CONFIRM_ACTION_REQUEST_FIELD_NUMBER: _ClassVar[int]
    CANCEL_SESSION_REQUEST_FIELD_NUMBER: _ClassVar[int]
    STREAM_MESSAGES_REQUEST_FIELD_NUMBER: _ClassVar[int]
    STOP_STREAM_MESSAGES_REQUEST_FIELD_NUMBER: _ClassVar[int]
    LIST_FILES_REQUEST_FIELD_NUMBER: _ClassVar[int]
    DELETE_FILE_REQUEST_FIELD_NUMBER: _ClassVar[int]
    SET_MCPS_REQUEST_FIELD_NUMBER: _ClassVar[int]
    SET_CONFIRMATION_CONFIG_REQUEST_FIELD_NUMBER: _ClassVar[int]
    GET_CONFIRMATION_INFO_REQUEST_FIELD_NUMBER: _ClassVar[int]
    req_id: str
    session_id: str
    register: RegisterRequest
    create_session_request: CreateSessionRequest
    delete_session_request: DeleteSessionRequest
    pause_session_request: PauseSessionRequest
    resume_session_request: ResumeSessionRequest
    list_mcps_request: ListMcpsRequest
    list_skills_request: ListSkillsRequest
    list_sessions_request: ListSessionsRequest
    prompt_request: PromptRequest
    confirm_action_request: ConfirmActionRequest
    cancel_session_request: CancelSessionRequest
    stream_messages_request: StreamMessagesRequest
    stop_stream_messages_request: StopStreamMessagesRequest
    list_files_request: ListFilesRequest
    delete_file_request: DeleteFileRequest
    set_mcps_request: SetMcpsRequest
    set_confirmation_config_request: SetConfirmationConfigRequest
    get_confirmation_info_request: GetConfirmationInfoRequest
    def __init__(self, req_id: _Optional[str] = ..., session_id: _Optional[str] = ..., register: _Optional[_Union[RegisterRequest, _Mapping]] = ..., create_session_request: _Optional[_Union[CreateSessionRequest, _Mapping]] = ..., delete_session_request: _Optional[_Union[DeleteSessionRequest, _Mapping]] = ..., pause_session_request: _Optional[_Union[PauseSessionRequest, _Mapping]] = ..., resume_session_request: _Optional[_Union[ResumeSessionRequest, _Mapping]] = ..., list_mcps_request: _Optional[_Union[ListMcpsRequest, _Mapping]] = ..., list_skills_request: _Optional[_Union[ListSkillsRequest, _Mapping]] = ..., list_sessions_request: _Optional[_Union[ListSessionsRequest, _Mapping]] = ..., prompt_request: _Optional[_Union[PromptRequest, _Mapping]] = ..., confirm_action_request: _Optional[_Union[ConfirmActionRequest, _Mapping]] = ..., cancel_session_request: _Optional[_Union[CancelSessionRequest, _Mapping]] = ..., stream_messages_request: _Optional[_Union[StreamMessagesRequest, _Mapping]] = ..., stop_stream_messages_request: _Optional[_Union[StopStreamMessagesRequest, _Mapping]] = ..., list_files_request: _Optional[_Union[ListFilesRequest, _Mapping]] = ..., delete_file_request: _Optional[_Union[DeleteFileRequest, _Mapping]] = ..., set_mcps_request: _Optional[_Union[SetMcpsRequest, _Mapping]] = ..., set_confirmation_config_request: _Optional[_Union[SetConfirmationConfigRequest, _Mapping]] = ..., get_confirmation_info_request: _Optional[_Union[GetConfirmationInfoRequest, _Mapping]] = ...) -> None: ...

class RegisterRequest(_message.Message):
    __slots__ = ("api_key",)
    API_KEY_FIELD_NUMBER: _ClassVar[int]
    api_key: str
    def __init__(self, api_key: _Optional[str] = ...) -> None: ...

class CreateSessionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListMcpsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListSkillsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListSessionsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PromptRequest(_message.Message):
    __slots__ = ("prompt", "meta")
    class MetaEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PROMPT_FIELD_NUMBER: _ClassVar[int]
    META_FIELD_NUMBER: _ClassVar[int]
    prompt: str
    meta: _containers.ScalarMap[str, str]
    def __init__(self, prompt: _Optional[str] = ..., meta: _Optional[_Mapping[str, str]] = ...) -> None: ...

class DeleteSessionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ConfirmActionRequest(_message.Message):
    __slots__ = ("confirmation_id", "confirmation_response")
    CONFIRMATION_ID_FIELD_NUMBER: _ClassVar[int]
    CONFIRMATION_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    confirmation_id: str
    confirmation_response: bool
    def __init__(self, confirmation_id: _Optional[str] = ..., confirmation_response: bool = ...) -> None: ...

class CancelSessionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StreamMessagesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StopStreamMessagesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListFilesRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SetMcpsRequest(_message.Message):
    __slots__ = ("mcp_servers",)
    MCP_SERVERS_FIELD_NUMBER: _ClassVar[int]
    mcp_servers: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, mcp_servers: _Optional[_Iterable[str]] = ...) -> None: ...

class GetConfirmationInfoRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SetConfirmationConfigRequest(_message.Message):
    __slots__ = ("always_ask_for_tool_confirmation",)
    ALWAYS_ASK_FOR_TOOL_CONFIRMATION_FIELD_NUMBER: _ClassVar[int]
    always_ask_for_tool_confirmation: bool
    def __init__(self, always_ask_for_tool_confirmation: bool = ...) -> None: ...

class ServerMessage(_message.Message):
    __slots__ = ("req_id", "register_response", "create_session_response", "delete_session_response", "pause_session_response", "resume_session_response", "list_mcps_response", "list_skills_response", "list_sessions_response", "prompt_response", "confirm_action_response", "cancel_session_response", "message", "session_state_change", "session_not_found", "list_files_response", "delete_file_response", "set_mcps_response", "set_confirmation_config_response", "get_confirmation_info_response")
    REQ_ID_FIELD_NUMBER: _ClassVar[int]
    REGISTER_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    CREATE_SESSION_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    DELETE_SESSION_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    PAUSE_SESSION_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    RESUME_SESSION_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    LIST_MCPS_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    LIST_SKILLS_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    LIST_SESSIONS_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    PROMPT_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    CONFIRM_ACTION_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    CANCEL_SESSION_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SESSION_STATE_CHANGE_FIELD_NUMBER: _ClassVar[int]
    SESSION_NOT_FOUND_FIELD_NUMBER: _ClassVar[int]
    LIST_FILES_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    DELETE_FILE_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    SET_MCPS_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    SET_CONFIRMATION_CONFIG_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    GET_CONFIRMATION_INFO_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    req_id: str
    register_response: RegisterResponse
    create_session_response: CreateSessionResponse
    delete_session_response: DeleteSessionResponse
    pause_session_response: PauseSessionResponse
    resume_session_response: ResumeSessionResponse
    list_mcps_response: ListMcpsResponse
    list_skills_response: ListSkillsResponse
    list_sessions_response: ListSessionsResponse
    prompt_response: PromptResponse
    confirm_action_response: ConfirmActionResponse
    cancel_session_response: CancelSessionResponse
    message: Message
    session_state_change: SessionStateChange
    session_not_found: SessionNotFound
    list_files_response: ListFilesResponse
    delete_file_response: DeleteFileResponse
    set_mcps_response: SetMcpsResponse
    set_confirmation_config_response: SetConfirmationConfigResponse
    get_confirmation_info_response: GetConfirmationInfoResponse
    def __init__(self, req_id: _Optional[str] = ..., register_response: _Optional[_Union[RegisterResponse, _Mapping]] = ..., create_session_response: _Optional[_Union[CreateSessionResponse, _Mapping]] = ..., delete_session_response: _Optional[_Union[DeleteSessionResponse, _Mapping]] = ..., pause_session_response: _Optional[_Union[PauseSessionResponse, _Mapping]] = ..., resume_session_response: _Optional[_Union[ResumeSessionResponse, _Mapping]] = ..., list_mcps_response: _Optional[_Union[ListMcpsResponse, _Mapping]] = ..., list_skills_response: _Optional[_Union[ListSkillsResponse, _Mapping]] = ..., list_sessions_response: _Optional[_Union[ListSessionsResponse, _Mapping]] = ..., prompt_response: _Optional[_Union[PromptResponse, _Mapping]] = ..., confirm_action_response: _Optional[_Union[ConfirmActionResponse, _Mapping]] = ..., cancel_session_response: _Optional[_Union[CancelSessionResponse, _Mapping]] = ..., message: _Optional[_Union[Message, _Mapping]] = ..., session_state_change: _Optional[_Union[SessionStateChange, _Mapping]] = ..., session_not_found: _Optional[_Union[SessionNotFound, _Mapping]] = ..., list_files_response: _Optional[_Union[ListFilesResponse, _Mapping]] = ..., delete_file_response: _Optional[_Union[DeleteFileResponse, _Mapping]] = ..., set_mcps_response: _Optional[_Union[SetMcpsResponse, _Mapping]] = ..., set_confirmation_config_response: _Optional[_Union[SetConfirmationConfigResponse, _Mapping]] = ..., get_confirmation_info_response: _Optional[_Union[GetConfirmationInfoResponse, _Mapping]] = ...) -> None: ...

class RegisterResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class CreateSessionResponse(_message.Message):
    __slots__ = ("success", "session_id")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    success: bool
    session_id: str
    def __init__(self, success: bool = ..., session_id: _Optional[str] = ...) -> None: ...

class DeleteSessionResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class PauseSessionRequest(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class ResumeSessionRequest(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class DeleteFileRequest(_message.Message):
    __slots__ = ("session_id", "filename")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    filename: str
    def __init__(self, session_id: _Optional[str] = ..., filename: _Optional[str] = ...) -> None: ...

class DeleteFileResponse(_message.Message):
    __slots__ = ("success", "error_message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    error_message: str
    def __init__(self, success: bool = ..., error_message: _Optional[str] = ...) -> None: ...

class PauseSessionResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class ResumeSessionResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class GetConfirmationInfoResponse(_message.Message):
    __slots__ = ("success", "confirmation_info")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    CONFIRMATION_INFO_FIELD_NUMBER: _ClassVar[int]
    success: bool
    confirmation_info: ToolCallConfirmationInfo
    def __init__(self, success: bool = ..., confirmation_info: _Optional[_Union[ToolCallConfirmationInfo, _Mapping]] = ...) -> None: ...

class ListMcpsResponse(_message.Message):
    __slots__ = ("success", "mcps")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MCPS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    mcps: _containers.RepeatedCompositeFieldContainer[McpInfo]
    def __init__(self, success: bool = ..., mcps: _Optional[_Iterable[_Union[McpInfo, _Mapping]]] = ...) -> None: ...

class ListSkillsResponse(_message.Message):
    __slots__ = ("success", "mcps")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MCPS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    mcps: _containers.RepeatedCompositeFieldContainer[McpInfo]
    def __init__(self, success: bool = ..., mcps: _Optional[_Iterable[_Union[McpInfo, _Mapping]]] = ...) -> None: ...

class ListSessionsResponse(_message.Message):
    __slots__ = ("success", "sessions")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    SESSIONS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    sessions: _containers.RepeatedCompositeFieldContainer[SessionInfo]
    def __init__(self, success: bool = ..., sessions: _Optional[_Iterable[_Union[SessionInfo, _Mapping]]] = ...) -> None: ...

class PromptResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class ConfirmActionResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class CancelSessionResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class SessionStateChange(_message.Message):
    __slots__ = ("session_id", "status")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    status: JobStatus
    def __init__(self, session_id: _Optional[str] = ..., status: _Optional[_Union[JobStatus, str]] = ...) -> None: ...

class SessionNotFound(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    def __init__(self, session_id: _Optional[str] = ...) -> None: ...

class FileInfo(_message.Message):
    __slots__ = ("filename", "content_type", "url", "session_id")
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    filename: str
    content_type: str
    url: str
    session_id: str
    def __init__(self, filename: _Optional[str] = ..., content_type: _Optional[str] = ..., url: _Optional[str] = ..., session_id: _Optional[str] = ...) -> None: ...

class ListFilesResponse(_message.Message):
    __slots__ = ("success", "files")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    FILES_FIELD_NUMBER: _ClassVar[int]
    success: bool
    files: _containers.RepeatedCompositeFieldContainer[FileInfo]
    def __init__(self, success: bool = ..., files: _Optional[_Iterable[_Union[FileInfo, _Mapping]]] = ...) -> None: ...

class SetMcpsResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class SetConfirmationConfigResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class FileMetadata(_message.Message):
    __slots__ = ("filename", "content_type", "session_id")
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    filename: str
    content_type: str
    session_id: str
    def __init__(self, filename: _Optional[str] = ..., content_type: _Optional[str] = ..., session_id: _Optional[str] = ...) -> None: ...

class UploadFileRequest(_message.Message):
    __slots__ = ("metadata", "chunk")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    CHUNK_FIELD_NUMBER: _ClassVar[int]
    metadata: FileMetadata
    chunk: bytes
    def __init__(self, metadata: _Optional[_Union[FileMetadata, _Mapping]] = ..., chunk: _Optional[bytes] = ...) -> None: ...

class UploadFileResponse(_message.Message):
    __slots__ = ("success", "error_message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    error_message: str
    def __init__(self, success: bool = ..., error_message: _Optional[str] = ...) -> None: ...

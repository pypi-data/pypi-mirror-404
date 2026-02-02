from . import api_pb2

API_HUB_HOST = "api-hub-171354917004.us-central1.run.app"

SESSION_EVENT_STATUS = "status"

# ClientMessage fields
_fields = api_pb2.ClientMessage.DESCRIPTOR.fields_by_name  # type: ignore
MSG_REGISTER = _fields["register"].name
MSG_CREATE_SESSION = _fields["create_session_request"].name
MSG_LIST_MCPS = _fields["list_mcps_request"].name
MSG_LIST_SKILLS = _fields["list_skills_request"].name
MSG_LIST_SESSIONS = _fields["list_sessions_request"].name
MSG_PROMPT = _fields["prompt_request"].name
MSG_DELETE_SESSION = _fields["delete_session_request"].name
MSG_PAUSE_SESSION = _fields["pause_session_request"].name
MSG_RESUME_SESSION = _fields["resume_session_request"].name
MSG_CONFIRM_ACTION = _fields["confirm_action_request"].name
MSG_CANCEL_SESSION = _fields["cancel_session_request"].name
MSG_STREAM_MESSAGES = _fields["stream_messages_request"].name
MSG_STOP_STREAM_MESSAGES = _fields["stop_stream_messages_request"].name
MSG_LIST_FILES = _fields["list_files_request"].name
MSG_DELETE_FILE = _fields["delete_file_request"].name
MSG_GET_CONFIRMATION_INFO = _fields["get_confirmation_info_request"].name
MSG_SET_MCPS = _fields["set_mcps_request"].name
MSG_SET_CONFIRMATION_CONFIG = _fields["set_confirmation_config_request"].name

# ServerMessage fields
_server_fields = api_pb2.ServerMessage.DESCRIPTOR.fields_by_name  # type: ignore
SERVER_MSG_REGISTER_RESPONSE = _server_fields["register_response"].name
SERVER_MSG_CREATE_SESSION_RESPONSE = _server_fields["create_session_response"].name
SERVER_MSG_DELETE_SESSION_RESPONSE = _server_fields["delete_session_response"].name
SERVER_MSG_LIST_MCPS_RESPONSE = _server_fields["list_mcps_response"].name
SERVER_MSG_LIST_SKILLS_RESPONSE = _server_fields["list_skills_response"].name
SERVER_MSG_LIST_SESSIONS_RESPONSE = _server_fields["list_sessions_response"].name
SERVER_MSG_MESSAGE = _server_fields["message"].name
SERVER_MSG_SESSION_STATE_CHANGE = _server_fields["session_state_change"].name
SERVER_MSG_LIST_FILES_RESPONSE = _server_fields["list_files_response"].name
SERVER_MSG_DELETE_FILE_RESPONSE = _server_fields["delete_file_response"].name
SERVER_MSG_GET_CONFIRMATION_INFO_RESPONSE = _server_fields[
    "get_confirmation_info_response"
].name
SERVER_MSG_SET_MCPS_RESPONSE = _server_fields["set_mcps_response"].name
SERVER_MSG_SET_CONFIRMATION_CONFIG_RESPONSE = _server_fields[
    "set_confirmation_config_response"
].name

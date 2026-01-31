from enum import Enum


class RunField(str, Enum):
    ENDED_AT = "ended_at"
    ERROR = "error"
    INPUT_ATTACHMENT_IDS = "input_attachment_ids"
    INPUT_VALUES = "input_values"
    MACHINE_ID = "machine_id"
    ORGANIZATION_ID = "organization_id"
    OUTPUT_ATTACHMENT_IDS = "output_attachment_ids"
    OUTPUT_DATA = "output_data"
    POOL_IDS = "pool_ids"
    RELEASE_SESSION_AFTER = "release_session_after"
    RUN_MESSAGE_HISTORY = "run_message_history"
    SENSITIVE_INPUT_ALIASES = "sensitive_input_aliases"
    SESSION_ALIAS = "session_alias"
    SESSION_ID = "session_id"
    STARTED_AT = "started_at"
    USAGE_METADATA = "usage_metadata"
    USER_ID = "user_id"

    def __str__(self) -> str:
        return str(self.value)

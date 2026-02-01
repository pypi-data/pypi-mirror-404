from enum import Enum

class PostPublicEnvelopeAddAttachmentResponse400ErrorCode(str, Enum):
    DOCUMENT_INVALID = "DOCUMENT_INVALID"
    ENVELOPE_NOT_FOUND = "ENVELOPE_NOT_FOUND"
    ENVELOPE_NOT_IN_DRAFT = "ENVELOPE_NOT_IN_DRAFT"
    FILE_SIZE_EXCEEDED = "FILE_SIZE_EXCEEDED"
    INVALID_REQUEST_FORMAT = "INVALID_REQUEST_FORMAT"
    WORKSPACE_NOT_FOUND = "WORKSPACE_NOT_FOUND"

    def __str__(self) -> str:
        return str(self.value)

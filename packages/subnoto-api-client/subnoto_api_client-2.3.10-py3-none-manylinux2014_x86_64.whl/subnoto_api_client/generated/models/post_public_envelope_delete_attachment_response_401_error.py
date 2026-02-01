from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.post_public_envelope_delete_attachment_response_401_error_code import PostPublicEnvelopeDeleteAttachmentResponse401ErrorCode






T = TypeVar("T", bound="PostPublicEnvelopeDeleteAttachmentResponse401Error")



@_attrs_define
class PostPublicEnvelopeDeleteAttachmentResponse401Error:
    """ 
        Attributes:
            code (PostPublicEnvelopeDeleteAttachmentResponse401ErrorCode): The error code
            message (str): The error message
            suggestion (str): A suggestion to resolve the error
            documentation_url (str): A URL to the documentation
     """

    code: PostPublicEnvelopeDeleteAttachmentResponse401ErrorCode
    message: str
    suggestion: str
    documentation_url: str





    def to_dict(self) -> dict[str, Any]:
        code = self.code.value

        message = self.message

        suggestion = self.suggestion

        documentation_url = self.documentation_url


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "code": code,
            "message": message,
            "suggestion": suggestion,
            "documentationUrl": documentation_url,
        })

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        code = PostPublicEnvelopeDeleteAttachmentResponse401ErrorCode(d.pop("code"))




        message = d.pop("message")

        suggestion = d.pop("suggestion")

        documentation_url = d.pop("documentationUrl")

        post_public_envelope_delete_attachment_response_401_error = cls(
            code=code,
            message=message,
            suggestion=suggestion,
            documentation_url=documentation_url,
        )

        return post_public_envelope_delete_attachment_response_401_error


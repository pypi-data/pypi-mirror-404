from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset







T = TypeVar("T", bound="PostPublicEnvelopeAddAttachmentResponse200")



@_attrs_define
class PostPublicEnvelopeAddAttachmentResponse200:
    """ 
        Attributes:
            document_uuid (str): The unique identifier of the created document.
            revision_encryption_key (str): The key in base64 for the document revision.
     """

    document_uuid: str
    revision_encryption_key: str





    def to_dict(self) -> dict[str, Any]:
        document_uuid = self.document_uuid

        revision_encryption_key = self.revision_encryption_key


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "documentUuid": document_uuid,
            "revisionEncryptionKey": revision_encryption_key,
        })

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        document_uuid = d.pop("documentUuid")

        revision_encryption_key = d.pop("revisionEncryptionKey")

        post_public_envelope_add_attachment_response_200 = cls(
            document_uuid=document_uuid,
            revision_encryption_key=revision_encryption_key,
        )

        return post_public_envelope_add_attachment_response_200


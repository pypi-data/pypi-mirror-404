from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset







T = TypeVar("T", bound="PostPublicEnvelopeCreateFromFileResponse200")



@_attrs_define
class PostPublicEnvelopeCreateFromFileResponse200:
    """ 
        Attributes:
            envelope_uuid (str): The unique identifier of the created envelope.
            document_uuid (str): The unique identifier of the first document.
     """

    envelope_uuid: str
    document_uuid: str





    def to_dict(self) -> dict[str, Any]:
        envelope_uuid = self.envelope_uuid

        document_uuid = self.document_uuid


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "envelopeUuid": envelope_uuid,
            "documentUuid": document_uuid,
        })

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        envelope_uuid = d.pop("envelopeUuid")

        document_uuid = d.pop("documentUuid")

        post_public_envelope_create_from_file_response_200 = cls(
            envelope_uuid=envelope_uuid,
            document_uuid=document_uuid,
        )

        return post_public_envelope_create_from_file_response_200


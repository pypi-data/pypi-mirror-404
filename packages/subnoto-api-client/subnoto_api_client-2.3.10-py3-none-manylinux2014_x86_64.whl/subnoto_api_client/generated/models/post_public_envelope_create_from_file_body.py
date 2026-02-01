from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field
import json
from .. import types

from ..types import UNSET, Unset

from ..types import UNSET, Unset






T = TypeVar("T", bound="PostPublicEnvelopeCreateFromFileBody")



@_attrs_define
class PostPublicEnvelopeCreateFromFileBody:
    """ 
        Attributes:
            workspace_uuid (str): The UUID of the workspace to create the envelope in.
            envelope_title (str): The title of the envelope being created.
            file (Any): The file to upload (PDF, Word, ODT, or RTF document, max 50MB).
            detect_smart_anchors (str | Unset): Enable Smart Anchor detection. Set to 'true' to detect and process Smart
                Anchors in the PDF. Defaults to false.
     """

    workspace_uuid: str
    envelope_title: str
    file: Any
    detect_smart_anchors: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        workspace_uuid = self.workspace_uuid

        envelope_title = self.envelope_title

        file = self.file

        detect_smart_anchors = self.detect_smart_anchors


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "workspaceUuid": workspace_uuid,
            "envelopeTitle": envelope_title,
            "file": file,
        })
        if detect_smart_anchors is not UNSET:
            field_dict["detectSmartAnchors"] = detect_smart_anchors

        return field_dict


    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("workspaceUuid", (None, str(self.workspace_uuid).encode(), "text/plain")))



        files.append(("envelopeTitle", (None, str(self.envelope_title).encode(), "text/plain")))



        files.append(("file", (None, str(self.file).encode(), "text/plain")))



        if not isinstance(self.detect_smart_anchors, Unset):
            files.append(("detectSmartAnchors", (None, str(self.detect_smart_anchors).encode(), "text/plain")))




        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))



        return files


    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        workspace_uuid = d.pop("workspaceUuid")

        envelope_title = d.pop("envelopeTitle")

        file = d.pop("file")

        detect_smart_anchors = d.pop("detectSmartAnchors", UNSET)

        post_public_envelope_create_from_file_body = cls(
            workspace_uuid=workspace_uuid,
            envelope_title=envelope_title,
            file=file,
            detect_smart_anchors=detect_smart_anchors,
        )


        post_public_envelope_create_from_file_body.additional_properties = d
        return post_public_envelope_create_from_file_body

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties

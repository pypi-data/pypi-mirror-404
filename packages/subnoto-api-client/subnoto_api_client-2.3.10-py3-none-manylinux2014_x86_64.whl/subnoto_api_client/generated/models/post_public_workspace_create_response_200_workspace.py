from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset







T = TypeVar("T", bound="PostPublicWorkspaceCreateResponse200Workspace")



@_attrs_define
class PostPublicWorkspaceCreateResponse200Workspace:
    """ 
        Attributes:
            uuid (str): The unique identifier of the workspace.
            name (str): The name of the workspace.
            creation_date (float): The date and time the workspace was created (unix timestamp).
            update_date (float): The date and time the workspace was last updated (unix timestamp).
            is_default (bool): Indicates whether this workspace is the default workspace for the users of the team.
            color_hex (str): The color of the workspace in hexadecimal format.
     """

    uuid: str
    name: str
    creation_date: float
    update_date: float
    is_default: bool
    color_hex: str





    def to_dict(self) -> dict[str, Any]:
        uuid = self.uuid

        name = self.name

        creation_date = self.creation_date

        update_date = self.update_date

        is_default = self.is_default

        color_hex = self.color_hex


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "uuid": uuid,
            "name": name,
            "creationDate": creation_date,
            "updateDate": update_date,
            "isDefault": is_default,
            "colorHex": color_hex,
        })

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        uuid = d.pop("uuid")

        name = d.pop("name")

        creation_date = d.pop("creationDate")

        update_date = d.pop("updateDate")

        is_default = d.pop("isDefault")

        color_hex = d.pop("colorHex")

        post_public_workspace_create_response_200_workspace = cls(
            uuid=uuid,
            name=name,
            creation_date=creation_date,
            update_date=update_date,
            is_default=is_default,
            color_hex=color_hex,
        )

        return post_public_workspace_create_response_200_workspace


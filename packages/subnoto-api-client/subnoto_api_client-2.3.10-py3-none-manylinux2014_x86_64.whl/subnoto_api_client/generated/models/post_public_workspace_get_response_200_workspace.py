from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset







T = TypeVar("T", bound="PostPublicWorkspaceGetResponse200Workspace")



@_attrs_define
class PostPublicWorkspaceGetResponse200Workspace:
    """ 
        Attributes:
            uuid (str): The unique identifier of the workspace.
            name (str): The name of the workspace.
            creation_date (float): The date and time the workspace was created (unix timestamp).
            update_date (float): The date and time the workspace was last updated (unix timestamp).
            is_default (bool): Indicates whether this workspace is the default workspace for the users of the team.
            color_hex (str): The color of the workspace in hexadecimal format.
            members_count (float): The number of members in this workspace.
     """

    uuid: str
    name: str
    creation_date: float
    update_date: float
    is_default: bool
    color_hex: str
    members_count: float





    def to_dict(self) -> dict[str, Any]:
        uuid = self.uuid

        name = self.name

        creation_date = self.creation_date

        update_date = self.update_date

        is_default = self.is_default

        color_hex = self.color_hex

        members_count = self.members_count


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "uuid": uuid,
            "name": name,
            "creationDate": creation_date,
            "updateDate": update_date,
            "isDefault": is_default,
            "colorHex": color_hex,
            "membersCount": members_count,
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

        members_count = d.pop("membersCount")

        post_public_workspace_get_response_200_workspace = cls(
            uuid=uuid,
            name=name,
            creation_date=creation_date,
            update_date=update_date,
            is_default=is_default,
            color_hex=color_hex,
            members_count=members_count,
        )

        return post_public_workspace_get_response_200_workspace


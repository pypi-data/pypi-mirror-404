from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset






T = TypeVar("T", bound="PostPublicWorkspaceCreateBody")



@_attrs_define
class PostPublicWorkspaceCreateBody:
    """ 
        Attributes:
            name (str): The name of the workspace to create.
            color_hex (str | Unset): The color of the workspace in hexadecimal format.
     """

    name: str
    color_hex: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        name = self.name

        color_hex = self.color_hex


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
        })
        if color_hex is not UNSET:
            field_dict["colorHex"] = color_hex

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        color_hex = d.pop("colorHex", UNSET)

        post_public_workspace_create_body = cls(
            name=name,
            color_hex=color_hex,
        )


        post_public_workspace_create_body.additional_properties = d
        return post_public_workspace_create_body

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

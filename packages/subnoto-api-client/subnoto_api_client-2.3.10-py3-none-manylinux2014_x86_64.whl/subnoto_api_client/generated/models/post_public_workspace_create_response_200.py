from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
  from ..models.post_public_workspace_create_response_200_workspace import PostPublicWorkspaceCreateResponse200Workspace





T = TypeVar("T", bound="PostPublicWorkspaceCreateResponse200")



@_attrs_define
class PostPublicWorkspaceCreateResponse200:
    """ 
        Attributes:
            workspace (PostPublicWorkspaceCreateResponse200Workspace):
     """

    workspace: PostPublicWorkspaceCreateResponse200Workspace





    def to_dict(self) -> dict[str, Any]:
        from ..models.post_public_workspace_create_response_200_workspace import PostPublicWorkspaceCreateResponse200Workspace
        workspace = self.workspace.to_dict()


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "workspace": workspace,
        })

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_public_workspace_create_response_200_workspace import PostPublicWorkspaceCreateResponse200Workspace
        d = dict(src_dict)
        workspace = PostPublicWorkspaceCreateResponse200Workspace.from_dict(d.pop("workspace"))




        post_public_workspace_create_response_200 = cls(
            workspace=workspace,
        )

        return post_public_workspace_create_response_200


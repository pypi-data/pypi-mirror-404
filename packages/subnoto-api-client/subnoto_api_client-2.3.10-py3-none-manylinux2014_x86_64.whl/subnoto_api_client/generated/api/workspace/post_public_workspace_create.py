from http import HTTPStatus
from typing import Any, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.post_public_workspace_create_body import PostPublicWorkspaceCreateBody
from ...models.post_public_workspace_create_response_200 import PostPublicWorkspaceCreateResponse200
from ...models.post_public_workspace_create_response_401 import PostPublicWorkspaceCreateResponse401
from ...models.post_public_workspace_create_response_403 import PostPublicWorkspaceCreateResponse403
from ...models.post_public_workspace_create_response_500 import PostPublicWorkspaceCreateResponse500
from typing import cast



def _get_kwargs(
    *,
    body: PostPublicWorkspaceCreateBody,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}


    

    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/public/workspace/create",
    }

    _kwargs["json"] = body.to_dict()


    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> PostPublicWorkspaceCreateResponse200 | PostPublicWorkspaceCreateResponse401 | PostPublicWorkspaceCreateResponse403 | PostPublicWorkspaceCreateResponse500 | None:
    if response.status_code == 200:
        response_200 = PostPublicWorkspaceCreateResponse200.from_dict(response.json())



        return response_200

    if response.status_code == 401:
        response_401 = PostPublicWorkspaceCreateResponse401.from_dict(response.json())



        return response_401

    if response.status_code == 403:
        response_403 = PostPublicWorkspaceCreateResponse403.from_dict(response.json())



        return response_403

    if response.status_code == 500:
        response_500 = PostPublicWorkspaceCreateResponse500.from_dict(response.json())



        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[PostPublicWorkspaceCreateResponse200 | PostPublicWorkspaceCreateResponse401 | PostPublicWorkspaceCreateResponse403 | PostPublicWorkspaceCreateResponse500]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostPublicWorkspaceCreateBody,

) -> Response[PostPublicWorkspaceCreateResponse200 | PostPublicWorkspaceCreateResponse401 | PostPublicWorkspaceCreateResponse403 | PostPublicWorkspaceCreateResponse500]:
    """ create

     Create a new workspace for the API key owner's team.

    Args:
        body (PostPublicWorkspaceCreateBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostPublicWorkspaceCreateResponse200 | PostPublicWorkspaceCreateResponse401 | PostPublicWorkspaceCreateResponse403 | PostPublicWorkspaceCreateResponse500]
     """


    kwargs = _get_kwargs(
        body=body,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    *,
    client: AuthenticatedClient | Client,
    body: PostPublicWorkspaceCreateBody,

) -> PostPublicWorkspaceCreateResponse200 | PostPublicWorkspaceCreateResponse401 | PostPublicWorkspaceCreateResponse403 | PostPublicWorkspaceCreateResponse500 | None:
    """ create

     Create a new workspace for the API key owner's team.

    Args:
        body (PostPublicWorkspaceCreateBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostPublicWorkspaceCreateResponse200 | PostPublicWorkspaceCreateResponse401 | PostPublicWorkspaceCreateResponse403 | PostPublicWorkspaceCreateResponse500
     """


    return sync_detailed(
        client=client,
body=body,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostPublicWorkspaceCreateBody,

) -> Response[PostPublicWorkspaceCreateResponse200 | PostPublicWorkspaceCreateResponse401 | PostPublicWorkspaceCreateResponse403 | PostPublicWorkspaceCreateResponse500]:
    """ create

     Create a new workspace for the API key owner's team.

    Args:
        body (PostPublicWorkspaceCreateBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostPublicWorkspaceCreateResponse200 | PostPublicWorkspaceCreateResponse401 | PostPublicWorkspaceCreateResponse403 | PostPublicWorkspaceCreateResponse500]
     """


    kwargs = _get_kwargs(
        body=body,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: PostPublicWorkspaceCreateBody,

) -> PostPublicWorkspaceCreateResponse200 | PostPublicWorkspaceCreateResponse401 | PostPublicWorkspaceCreateResponse403 | PostPublicWorkspaceCreateResponse500 | None:
    """ create

     Create a new workspace for the API key owner's team.

    Args:
        body (PostPublicWorkspaceCreateBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostPublicWorkspaceCreateResponse200 | PostPublicWorkspaceCreateResponse401 | PostPublicWorkspaceCreateResponse403 | PostPublicWorkspaceCreateResponse500
     """


    return (await asyncio_detailed(
        client=client,
body=body,

    )).parsed

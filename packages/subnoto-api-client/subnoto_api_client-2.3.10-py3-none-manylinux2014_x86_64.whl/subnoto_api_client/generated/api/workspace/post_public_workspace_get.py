from http import HTTPStatus
from typing import Any, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.post_public_workspace_get_body_type_0 import PostPublicWorkspaceGetBodyType0
from ...models.post_public_workspace_get_body_type_1 import PostPublicWorkspaceGetBodyType1
from ...models.post_public_workspace_get_response_200 import PostPublicWorkspaceGetResponse200
from ...models.post_public_workspace_get_response_400 import PostPublicWorkspaceGetResponse400
from ...models.post_public_workspace_get_response_401 import PostPublicWorkspaceGetResponse401
from ...models.post_public_workspace_get_response_403 import PostPublicWorkspaceGetResponse403
from ...models.post_public_workspace_get_response_500 import PostPublicWorkspaceGetResponse500
from typing import cast



def _get_kwargs(
    *,
    body: PostPublicWorkspaceGetBodyType0 | PostPublicWorkspaceGetBodyType1,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}


    

    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/public/workspace/get",
    }

    _kwargs["json"]: dict[str, Any]
    if isinstance(body, PostPublicWorkspaceGetBodyType0):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body.to_dict()



    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> PostPublicWorkspaceGetResponse200 | PostPublicWorkspaceGetResponse400 | PostPublicWorkspaceGetResponse401 | PostPublicWorkspaceGetResponse403 | PostPublicWorkspaceGetResponse500 | None:
    if response.status_code == 200:
        response_200 = PostPublicWorkspaceGetResponse200.from_dict(response.json())



        return response_200

    if response.status_code == 400:
        response_400 = PostPublicWorkspaceGetResponse400.from_dict(response.json())



        return response_400

    if response.status_code == 401:
        response_401 = PostPublicWorkspaceGetResponse401.from_dict(response.json())



        return response_401

    if response.status_code == 403:
        response_403 = PostPublicWorkspaceGetResponse403.from_dict(response.json())



        return response_403

    if response.status_code == 500:
        response_500 = PostPublicWorkspaceGetResponse500.from_dict(response.json())



        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[PostPublicWorkspaceGetResponse200 | PostPublicWorkspaceGetResponse400 | PostPublicWorkspaceGetResponse401 | PostPublicWorkspaceGetResponse403 | PostPublicWorkspaceGetResponse500]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostPublicWorkspaceGetBodyType0 | PostPublicWorkspaceGetBodyType1,

) -> Response[PostPublicWorkspaceGetResponse200 | PostPublicWorkspaceGetResponse400 | PostPublicWorkspaceGetResponse401 | PostPublicWorkspaceGetResponse403 | PostPublicWorkspaceGetResponse500]:
    """ get

     Get a workspace by UUID or name. Returns workspace details including member count.

    Args:
        body (PostPublicWorkspaceGetBodyType0 | PostPublicWorkspaceGetBodyType1):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostPublicWorkspaceGetResponse200 | PostPublicWorkspaceGetResponse400 | PostPublicWorkspaceGetResponse401 | PostPublicWorkspaceGetResponse403 | PostPublicWorkspaceGetResponse500]
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
    body: PostPublicWorkspaceGetBodyType0 | PostPublicWorkspaceGetBodyType1,

) -> PostPublicWorkspaceGetResponse200 | PostPublicWorkspaceGetResponse400 | PostPublicWorkspaceGetResponse401 | PostPublicWorkspaceGetResponse403 | PostPublicWorkspaceGetResponse500 | None:
    """ get

     Get a workspace by UUID or name. Returns workspace details including member count.

    Args:
        body (PostPublicWorkspaceGetBodyType0 | PostPublicWorkspaceGetBodyType1):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostPublicWorkspaceGetResponse200 | PostPublicWorkspaceGetResponse400 | PostPublicWorkspaceGetResponse401 | PostPublicWorkspaceGetResponse403 | PostPublicWorkspaceGetResponse500
     """


    return sync_detailed(
        client=client,
body=body,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostPublicWorkspaceGetBodyType0 | PostPublicWorkspaceGetBodyType1,

) -> Response[PostPublicWorkspaceGetResponse200 | PostPublicWorkspaceGetResponse400 | PostPublicWorkspaceGetResponse401 | PostPublicWorkspaceGetResponse403 | PostPublicWorkspaceGetResponse500]:
    """ get

     Get a workspace by UUID or name. Returns workspace details including member count.

    Args:
        body (PostPublicWorkspaceGetBodyType0 | PostPublicWorkspaceGetBodyType1):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostPublicWorkspaceGetResponse200 | PostPublicWorkspaceGetResponse400 | PostPublicWorkspaceGetResponse401 | PostPublicWorkspaceGetResponse403 | PostPublicWorkspaceGetResponse500]
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
    body: PostPublicWorkspaceGetBodyType0 | PostPublicWorkspaceGetBodyType1,

) -> PostPublicWorkspaceGetResponse200 | PostPublicWorkspaceGetResponse400 | PostPublicWorkspaceGetResponse401 | PostPublicWorkspaceGetResponse403 | PostPublicWorkspaceGetResponse500 | None:
    """ get

     Get a workspace by UUID or name. Returns workspace details including member count.

    Args:
        body (PostPublicWorkspaceGetBodyType0 | PostPublicWorkspaceGetBodyType1):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostPublicWorkspaceGetResponse200 | PostPublicWorkspaceGetResponse400 | PostPublicWorkspaceGetResponse401 | PostPublicWorkspaceGetResponse403 | PostPublicWorkspaceGetResponse500
     """


    return (await asyncio_detailed(
        client=client,
body=body,

    )).parsed

from http import HTTPStatus
from typing import Any, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.post_public_envelope_delete_attachment_body import PostPublicEnvelopeDeleteAttachmentBody
from ...models.post_public_envelope_delete_attachment_response_200 import PostPublicEnvelopeDeleteAttachmentResponse200
from ...models.post_public_envelope_delete_attachment_response_400 import PostPublicEnvelopeDeleteAttachmentResponse400
from ...models.post_public_envelope_delete_attachment_response_401 import PostPublicEnvelopeDeleteAttachmentResponse401
from ...models.post_public_envelope_delete_attachment_response_403 import PostPublicEnvelopeDeleteAttachmentResponse403
from ...models.post_public_envelope_delete_attachment_response_500 import PostPublicEnvelopeDeleteAttachmentResponse500
from typing import cast



def _get_kwargs(
    *,
    body: PostPublicEnvelopeDeleteAttachmentBody,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}


    

    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/public/envelope/delete-attachment",
    }

    _kwargs["json"] = body.to_dict()


    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> PostPublicEnvelopeDeleteAttachmentResponse200 | PostPublicEnvelopeDeleteAttachmentResponse400 | PostPublicEnvelopeDeleteAttachmentResponse401 | PostPublicEnvelopeDeleteAttachmentResponse403 | PostPublicEnvelopeDeleteAttachmentResponse500 | None:
    if response.status_code == 200:
        response_200 = PostPublicEnvelopeDeleteAttachmentResponse200.from_dict(response.json())



        return response_200

    if response.status_code == 400:
        response_400 = PostPublicEnvelopeDeleteAttachmentResponse400.from_dict(response.json())



        return response_400

    if response.status_code == 401:
        response_401 = PostPublicEnvelopeDeleteAttachmentResponse401.from_dict(response.json())



        return response_401

    if response.status_code == 403:
        response_403 = PostPublicEnvelopeDeleteAttachmentResponse403.from_dict(response.json())



        return response_403

    if response.status_code == 500:
        response_500 = PostPublicEnvelopeDeleteAttachmentResponse500.from_dict(response.json())



        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[PostPublicEnvelopeDeleteAttachmentResponse200 | PostPublicEnvelopeDeleteAttachmentResponse400 | PostPublicEnvelopeDeleteAttachmentResponse401 | PostPublicEnvelopeDeleteAttachmentResponse403 | PostPublicEnvelopeDeleteAttachmentResponse500]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostPublicEnvelopeDeleteAttachmentBody,

) -> Response[PostPublicEnvelopeDeleteAttachmentResponse200 | PostPublicEnvelopeDeleteAttachmentResponse400 | PostPublicEnvelopeDeleteAttachmentResponse401 | PostPublicEnvelopeDeleteAttachmentResponse403 | PostPublicEnvelopeDeleteAttachmentResponse500]:
    """ delete-attachment

     Delete an attachment document and its revisions

    Args:
        body (PostPublicEnvelopeDeleteAttachmentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostPublicEnvelopeDeleteAttachmentResponse200 | PostPublicEnvelopeDeleteAttachmentResponse400 | PostPublicEnvelopeDeleteAttachmentResponse401 | PostPublicEnvelopeDeleteAttachmentResponse403 | PostPublicEnvelopeDeleteAttachmentResponse500]
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
    body: PostPublicEnvelopeDeleteAttachmentBody,

) -> PostPublicEnvelopeDeleteAttachmentResponse200 | PostPublicEnvelopeDeleteAttachmentResponse400 | PostPublicEnvelopeDeleteAttachmentResponse401 | PostPublicEnvelopeDeleteAttachmentResponse403 | PostPublicEnvelopeDeleteAttachmentResponse500 | None:
    """ delete-attachment

     Delete an attachment document and its revisions

    Args:
        body (PostPublicEnvelopeDeleteAttachmentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostPublicEnvelopeDeleteAttachmentResponse200 | PostPublicEnvelopeDeleteAttachmentResponse400 | PostPublicEnvelopeDeleteAttachmentResponse401 | PostPublicEnvelopeDeleteAttachmentResponse403 | PostPublicEnvelopeDeleteAttachmentResponse500
     """


    return sync_detailed(
        client=client,
body=body,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostPublicEnvelopeDeleteAttachmentBody,

) -> Response[PostPublicEnvelopeDeleteAttachmentResponse200 | PostPublicEnvelopeDeleteAttachmentResponse400 | PostPublicEnvelopeDeleteAttachmentResponse401 | PostPublicEnvelopeDeleteAttachmentResponse403 | PostPublicEnvelopeDeleteAttachmentResponse500]:
    """ delete-attachment

     Delete an attachment document and its revisions

    Args:
        body (PostPublicEnvelopeDeleteAttachmentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostPublicEnvelopeDeleteAttachmentResponse200 | PostPublicEnvelopeDeleteAttachmentResponse400 | PostPublicEnvelopeDeleteAttachmentResponse401 | PostPublicEnvelopeDeleteAttachmentResponse403 | PostPublicEnvelopeDeleteAttachmentResponse500]
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
    body: PostPublicEnvelopeDeleteAttachmentBody,

) -> PostPublicEnvelopeDeleteAttachmentResponse200 | PostPublicEnvelopeDeleteAttachmentResponse400 | PostPublicEnvelopeDeleteAttachmentResponse401 | PostPublicEnvelopeDeleteAttachmentResponse403 | PostPublicEnvelopeDeleteAttachmentResponse500 | None:
    """ delete-attachment

     Delete an attachment document and its revisions

    Args:
        body (PostPublicEnvelopeDeleteAttachmentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostPublicEnvelopeDeleteAttachmentResponse200 | PostPublicEnvelopeDeleteAttachmentResponse400 | PostPublicEnvelopeDeleteAttachmentResponse401 | PostPublicEnvelopeDeleteAttachmentResponse403 | PostPublicEnvelopeDeleteAttachmentResponse500
     """


    return (await asyncio_detailed(
        client=client,
body=body,

    )).parsed

from http import HTTPStatus
from typing import Any, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.post_public_envelope_add_attachment_body import PostPublicEnvelopeAddAttachmentBody
from ...models.post_public_envelope_add_attachment_response_200 import PostPublicEnvelopeAddAttachmentResponse200
from ...models.post_public_envelope_add_attachment_response_400 import PostPublicEnvelopeAddAttachmentResponse400
from ...models.post_public_envelope_add_attachment_response_401 import PostPublicEnvelopeAddAttachmentResponse401
from ...models.post_public_envelope_add_attachment_response_403 import PostPublicEnvelopeAddAttachmentResponse403
from ...models.post_public_envelope_add_attachment_response_500 import PostPublicEnvelopeAddAttachmentResponse500
from typing import cast



def _get_kwargs(
    *,
    body: PostPublicEnvelopeAddAttachmentBody,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}


    

    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/public/envelope/add-attachment",
    }

    _kwargs["files"] = body.to_multipart()



    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> PostPublicEnvelopeAddAttachmentResponse200 | PostPublicEnvelopeAddAttachmentResponse400 | PostPublicEnvelopeAddAttachmentResponse401 | PostPublicEnvelopeAddAttachmentResponse403 | PostPublicEnvelopeAddAttachmentResponse500 | None:
    if response.status_code == 200:
        response_200 = PostPublicEnvelopeAddAttachmentResponse200.from_dict(response.json())



        return response_200

    if response.status_code == 400:
        response_400 = PostPublicEnvelopeAddAttachmentResponse400.from_dict(response.json())



        return response_400

    if response.status_code == 401:
        response_401 = PostPublicEnvelopeAddAttachmentResponse401.from_dict(response.json())



        return response_401

    if response.status_code == 403:
        response_403 = PostPublicEnvelopeAddAttachmentResponse403.from_dict(response.json())



        return response_403

    if response.status_code == 500:
        response_500 = PostPublicEnvelopeAddAttachmentResponse500.from_dict(response.json())



        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[PostPublicEnvelopeAddAttachmentResponse200 | PostPublicEnvelopeAddAttachmentResponse400 | PostPublicEnvelopeAddAttachmentResponse401 | PostPublicEnvelopeAddAttachmentResponse403 | PostPublicEnvelopeAddAttachmentResponse500]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostPublicEnvelopeAddAttachmentBody,

) -> Response[PostPublicEnvelopeAddAttachmentResponse200 | PostPublicEnvelopeAddAttachmentResponse400 | PostPublicEnvelopeAddAttachmentResponse401 | PostPublicEnvelopeAddAttachmentResponse403 | PostPublicEnvelopeAddAttachmentResponse500]:
    """ add-attachment

     Add a document attachment to an existing envelope. Accepts multipart/form-data with a PDF, Word
    (DOCX/DOC), ODT, or RTF document file.

    Args:
        body (PostPublicEnvelopeAddAttachmentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostPublicEnvelopeAddAttachmentResponse200 | PostPublicEnvelopeAddAttachmentResponse400 | PostPublicEnvelopeAddAttachmentResponse401 | PostPublicEnvelopeAddAttachmentResponse403 | PostPublicEnvelopeAddAttachmentResponse500]
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
    body: PostPublicEnvelopeAddAttachmentBody,

) -> PostPublicEnvelopeAddAttachmentResponse200 | PostPublicEnvelopeAddAttachmentResponse400 | PostPublicEnvelopeAddAttachmentResponse401 | PostPublicEnvelopeAddAttachmentResponse403 | PostPublicEnvelopeAddAttachmentResponse500 | None:
    """ add-attachment

     Add a document attachment to an existing envelope. Accepts multipart/form-data with a PDF, Word
    (DOCX/DOC), ODT, or RTF document file.

    Args:
        body (PostPublicEnvelopeAddAttachmentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostPublicEnvelopeAddAttachmentResponse200 | PostPublicEnvelopeAddAttachmentResponse400 | PostPublicEnvelopeAddAttachmentResponse401 | PostPublicEnvelopeAddAttachmentResponse403 | PostPublicEnvelopeAddAttachmentResponse500
     """


    return sync_detailed(
        client=client,
body=body,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostPublicEnvelopeAddAttachmentBody,

) -> Response[PostPublicEnvelopeAddAttachmentResponse200 | PostPublicEnvelopeAddAttachmentResponse400 | PostPublicEnvelopeAddAttachmentResponse401 | PostPublicEnvelopeAddAttachmentResponse403 | PostPublicEnvelopeAddAttachmentResponse500]:
    """ add-attachment

     Add a document attachment to an existing envelope. Accepts multipart/form-data with a PDF, Word
    (DOCX/DOC), ODT, or RTF document file.

    Args:
        body (PostPublicEnvelopeAddAttachmentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostPublicEnvelopeAddAttachmentResponse200 | PostPublicEnvelopeAddAttachmentResponse400 | PostPublicEnvelopeAddAttachmentResponse401 | PostPublicEnvelopeAddAttachmentResponse403 | PostPublicEnvelopeAddAttachmentResponse500]
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
    body: PostPublicEnvelopeAddAttachmentBody,

) -> PostPublicEnvelopeAddAttachmentResponse200 | PostPublicEnvelopeAddAttachmentResponse400 | PostPublicEnvelopeAddAttachmentResponse401 | PostPublicEnvelopeAddAttachmentResponse403 | PostPublicEnvelopeAddAttachmentResponse500 | None:
    """ add-attachment

     Add a document attachment to an existing envelope. Accepts multipart/form-data with a PDF, Word
    (DOCX/DOC), ODT, or RTF document file.

    Args:
        body (PostPublicEnvelopeAddAttachmentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostPublicEnvelopeAddAttachmentResponse200 | PostPublicEnvelopeAddAttachmentResponse400 | PostPublicEnvelopeAddAttachmentResponse401 | PostPublicEnvelopeAddAttachmentResponse403 | PostPublicEnvelopeAddAttachmentResponse500
     """


    return (await asyncio_detailed(
        client=client,
body=body,

    )).parsed

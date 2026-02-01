from http import HTTPStatus
from typing import Any, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.post_public_envelope_create_from_file_body import PostPublicEnvelopeCreateFromFileBody
from ...models.post_public_envelope_create_from_file_response_200 import PostPublicEnvelopeCreateFromFileResponse200
from ...models.post_public_envelope_create_from_file_response_400 import PostPublicEnvelopeCreateFromFileResponse400
from ...models.post_public_envelope_create_from_file_response_401 import PostPublicEnvelopeCreateFromFileResponse401
from ...models.post_public_envelope_create_from_file_response_403 import PostPublicEnvelopeCreateFromFileResponse403
from ...models.post_public_envelope_create_from_file_response_500 import PostPublicEnvelopeCreateFromFileResponse500
from typing import cast



def _get_kwargs(
    *,
    body: PostPublicEnvelopeCreateFromFileBody,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}


    

    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/public/envelope/create-from-file",
    }

    _kwargs["files"] = body.to_multipart()



    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> PostPublicEnvelopeCreateFromFileResponse200 | PostPublicEnvelopeCreateFromFileResponse400 | PostPublicEnvelopeCreateFromFileResponse401 | PostPublicEnvelopeCreateFromFileResponse403 | PostPublicEnvelopeCreateFromFileResponse500 | None:
    if response.status_code == 200:
        response_200 = PostPublicEnvelopeCreateFromFileResponse200.from_dict(response.json())



        return response_200

    if response.status_code == 400:
        response_400 = PostPublicEnvelopeCreateFromFileResponse400.from_dict(response.json())



        return response_400

    if response.status_code == 401:
        response_401 = PostPublicEnvelopeCreateFromFileResponse401.from_dict(response.json())



        return response_401

    if response.status_code == 403:
        response_403 = PostPublicEnvelopeCreateFromFileResponse403.from_dict(response.json())



        return response_403

    if response.status_code == 500:
        response_500 = PostPublicEnvelopeCreateFromFileResponse500.from_dict(response.json())



        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[PostPublicEnvelopeCreateFromFileResponse200 | PostPublicEnvelopeCreateFromFileResponse400 | PostPublicEnvelopeCreateFromFileResponse401 | PostPublicEnvelopeCreateFromFileResponse403 | PostPublicEnvelopeCreateFromFileResponse500]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostPublicEnvelopeCreateFromFileBody,

) -> Response[PostPublicEnvelopeCreateFromFileResponse200 | PostPublicEnvelopeCreateFromFileResponse400 | PostPublicEnvelopeCreateFromFileResponse401 | PostPublicEnvelopeCreateFromFileResponse403 | PostPublicEnvelopeCreateFromFileResponse500]:
    """ create-from-file

     Create an envelope and the first document placeholder with a file upload. Accepts multipart/form-
    data with a PDF, Word (DOCX/DOC), ODT, or RTF document file (max 50 MB). DOCX, ODT, and RTF files
    are converted to PDF. The file is processed and uploaded directly.

    Args:
        body (PostPublicEnvelopeCreateFromFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostPublicEnvelopeCreateFromFileResponse200 | PostPublicEnvelopeCreateFromFileResponse400 | PostPublicEnvelopeCreateFromFileResponse401 | PostPublicEnvelopeCreateFromFileResponse403 | PostPublicEnvelopeCreateFromFileResponse500]
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
    body: PostPublicEnvelopeCreateFromFileBody,

) -> PostPublicEnvelopeCreateFromFileResponse200 | PostPublicEnvelopeCreateFromFileResponse400 | PostPublicEnvelopeCreateFromFileResponse401 | PostPublicEnvelopeCreateFromFileResponse403 | PostPublicEnvelopeCreateFromFileResponse500 | None:
    """ create-from-file

     Create an envelope and the first document placeholder with a file upload. Accepts multipart/form-
    data with a PDF, Word (DOCX/DOC), ODT, or RTF document file (max 50 MB). DOCX, ODT, and RTF files
    are converted to PDF. The file is processed and uploaded directly.

    Args:
        body (PostPublicEnvelopeCreateFromFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostPublicEnvelopeCreateFromFileResponse200 | PostPublicEnvelopeCreateFromFileResponse400 | PostPublicEnvelopeCreateFromFileResponse401 | PostPublicEnvelopeCreateFromFileResponse403 | PostPublicEnvelopeCreateFromFileResponse500
     """


    return sync_detailed(
        client=client,
body=body,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostPublicEnvelopeCreateFromFileBody,

) -> Response[PostPublicEnvelopeCreateFromFileResponse200 | PostPublicEnvelopeCreateFromFileResponse400 | PostPublicEnvelopeCreateFromFileResponse401 | PostPublicEnvelopeCreateFromFileResponse403 | PostPublicEnvelopeCreateFromFileResponse500]:
    """ create-from-file

     Create an envelope and the first document placeholder with a file upload. Accepts multipart/form-
    data with a PDF, Word (DOCX/DOC), ODT, or RTF document file (max 50 MB). DOCX, ODT, and RTF files
    are converted to PDF. The file is processed and uploaded directly.

    Args:
        body (PostPublicEnvelopeCreateFromFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostPublicEnvelopeCreateFromFileResponse200 | PostPublicEnvelopeCreateFromFileResponse400 | PostPublicEnvelopeCreateFromFileResponse401 | PostPublicEnvelopeCreateFromFileResponse403 | PostPublicEnvelopeCreateFromFileResponse500]
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
    body: PostPublicEnvelopeCreateFromFileBody,

) -> PostPublicEnvelopeCreateFromFileResponse200 | PostPublicEnvelopeCreateFromFileResponse400 | PostPublicEnvelopeCreateFromFileResponse401 | PostPublicEnvelopeCreateFromFileResponse403 | PostPublicEnvelopeCreateFromFileResponse500 | None:
    """ create-from-file

     Create an envelope and the first document placeholder with a file upload. Accepts multipart/form-
    data with a PDF, Word (DOCX/DOC), ODT, or RTF document file (max 50 MB). DOCX, ODT, and RTF files
    are converted to PDF. The file is processed and uploaded directly.

    Args:
        body (PostPublicEnvelopeCreateFromFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostPublicEnvelopeCreateFromFileResponse200 | PostPublicEnvelopeCreateFromFileResponse400 | PostPublicEnvelopeCreateFromFileResponse401 | PostPublicEnvelopeCreateFromFileResponse403 | PostPublicEnvelopeCreateFromFileResponse500
     """


    return (await asyncio_detailed(
        client=client,
body=body,

    )).parsed

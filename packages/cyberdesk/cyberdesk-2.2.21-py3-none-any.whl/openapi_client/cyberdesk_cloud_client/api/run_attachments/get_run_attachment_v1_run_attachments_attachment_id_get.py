from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.run_attachment_response import RunAttachmentResponse
from ...types import Response


def _get_kwargs(
    attachment_id: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/run-attachments/{attachment_id}".format(
            attachment_id=quote(str(attachment_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | RunAttachmentResponse | None:
    if response.status_code == 200:
        response_200 = RunAttachmentResponse.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | RunAttachmentResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    attachment_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[HTTPValidationError | RunAttachmentResponse]:
    """Get Run Attachment

     Get a specific run attachment by ID.

    Returns attachment metadata only. Use the download endpoint to get file content.

    Args:
        attachment_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RunAttachmentResponse]
    """

    kwargs = _get_kwargs(
        attachment_id=attachment_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    attachment_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | RunAttachmentResponse | None:
    """Get Run Attachment

     Get a specific run attachment by ID.

    Returns attachment metadata only. Use the download endpoint to get file content.

    Args:
        attachment_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RunAttachmentResponse
    """

    return sync_detailed(
        attachment_id=attachment_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    attachment_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[HTTPValidationError | RunAttachmentResponse]:
    """Get Run Attachment

     Get a specific run attachment by ID.

    Returns attachment metadata only. Use the download endpoint to get file content.

    Args:
        attachment_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RunAttachmentResponse]
    """

    kwargs = _get_kwargs(
        attachment_id=attachment_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    attachment_id: UUID,
    *,
    client: AuthenticatedClient,
) -> HTTPValidationError | RunAttachmentResponse | None:
    """Get Run Attachment

     Get a specific run attachment by ID.

    Returns attachment metadata only. Use the download endpoint to get file content.

    Args:
        attachment_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RunAttachmentResponse
    """

    return (
        await asyncio_detailed(
            attachment_id=attachment_id,
            client=client,
        )
    ).parsed

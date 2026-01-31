from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.attachment_type import AttachmentType
from ...models.http_validation_error import HTTPValidationError
from ...models.paginated_response_run_attachment_response import PaginatedResponseRunAttachmentResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    run_id: None | Unset | UUID = UNSET,
    attachment_type: AttachmentType | None | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_run_id: None | str | Unset
    if isinstance(run_id, Unset):
        json_run_id = UNSET
    elif isinstance(run_id, UUID):
        json_run_id = str(run_id)
    else:
        json_run_id = run_id
    params["run_id"] = json_run_id

    json_attachment_type: None | str | Unset
    if isinstance(attachment_type, Unset):
        json_attachment_type = UNSET
    elif isinstance(attachment_type, AttachmentType):
        json_attachment_type = attachment_type.value
    else:
        json_attachment_type = attachment_type
    params["attachment_type"] = json_attachment_type

    params["skip"] = skip

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/run-attachments",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | PaginatedResponseRunAttachmentResponse | None:
    if response.status_code == 200:
        response_200 = PaginatedResponseRunAttachmentResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | PaginatedResponseRunAttachmentResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    run_id: None | Unset | UUID = UNSET,
    attachment_type: AttachmentType | None | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> Response[HTTPValidationError | PaginatedResponseRunAttachmentResponse]:
    """List Run Attachments

     List all run attachments for the authenticated organization.

    Supports pagination and filtering by run ID and attachment type.

    Args:
        run_id (None | Unset | UUID): Filter by run ID
        attachment_type (AttachmentType | None | Unset): Filter by attachment type
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PaginatedResponseRunAttachmentResponse]
    """

    kwargs = _get_kwargs(
        run_id=run_id,
        attachment_type=attachment_type,
        skip=skip,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    run_id: None | Unset | UUID = UNSET,
    attachment_type: AttachmentType | None | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> HTTPValidationError | PaginatedResponseRunAttachmentResponse | None:
    """List Run Attachments

     List all run attachments for the authenticated organization.

    Supports pagination and filtering by run ID and attachment type.

    Args:
        run_id (None | Unset | UUID): Filter by run ID
        attachment_type (AttachmentType | None | Unset): Filter by attachment type
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PaginatedResponseRunAttachmentResponse
    """

    return sync_detailed(
        client=client,
        run_id=run_id,
        attachment_type=attachment_type,
        skip=skip,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    run_id: None | Unset | UUID = UNSET,
    attachment_type: AttachmentType | None | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> Response[HTTPValidationError | PaginatedResponseRunAttachmentResponse]:
    """List Run Attachments

     List all run attachments for the authenticated organization.

    Supports pagination and filtering by run ID and attachment type.

    Args:
        run_id (None | Unset | UUID): Filter by run ID
        attachment_type (AttachmentType | None | Unset): Filter by attachment type
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PaginatedResponseRunAttachmentResponse]
    """

    kwargs = _get_kwargs(
        run_id=run_id,
        attachment_type=attachment_type,
        skip=skip,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    run_id: None | Unset | UUID = UNSET,
    attachment_type: AttachmentType | None | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> HTTPValidationError | PaginatedResponseRunAttachmentResponse | None:
    """List Run Attachments

     List all run attachments for the authenticated organization.

    Supports pagination and filtering by run ID and attachment type.

    Args:
        run_id (None | Unset | UUID): Filter by run ID
        attachment_type (AttachmentType | None | Unset): Filter by attachment type
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PaginatedResponseRunAttachmentResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            run_id=run_id,
            attachment_type=attachment_type,
            skip=skip,
            limit=limit,
        )
    ).parsed

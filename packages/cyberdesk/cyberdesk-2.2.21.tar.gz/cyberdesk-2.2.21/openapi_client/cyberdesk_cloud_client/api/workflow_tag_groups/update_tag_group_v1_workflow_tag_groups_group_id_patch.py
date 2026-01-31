from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.workflow_tag_group_response import WorkflowTagGroupResponse
from ...models.workflow_tag_group_update import WorkflowTagGroupUpdate
from ...types import UNSET, Response, Unset


def _get_kwargs(
    group_id: UUID,
    *,
    body: WorkflowTagGroupUpdate,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v1/workflow-tag-groups/{group_id}".format(
            group_id=quote(str(group_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | WorkflowTagGroupResponse | None:
    if response.status_code == 200:
        response_200 = WorkflowTagGroupResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | WorkflowTagGroupResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    group_id: UUID,
    *,
    client: AuthenticatedClient,
    body: WorkflowTagGroupUpdate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | WorkflowTagGroupResponse]:
    """Update Tag Group

     Update a workflow tag group.

    Args:
        group_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (WorkflowTagGroupUpdate): Schema for updating a workflow tag group

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | WorkflowTagGroupResponse]
    """

    kwargs = _get_kwargs(
        group_id=group_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    group_id: UUID,
    *,
    client: AuthenticatedClient,
    body: WorkflowTagGroupUpdate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | WorkflowTagGroupResponse | None:
    """Update Tag Group

     Update a workflow tag group.

    Args:
        group_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (WorkflowTagGroupUpdate): Schema for updating a workflow tag group

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | WorkflowTagGroupResponse
    """

    return sync_detailed(
        group_id=group_id,
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    group_id: UUID,
    *,
    client: AuthenticatedClient,
    body: WorkflowTagGroupUpdate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | WorkflowTagGroupResponse]:
    """Update Tag Group

     Update a workflow tag group.

    Args:
        group_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (WorkflowTagGroupUpdate): Schema for updating a workflow tag group

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | WorkflowTagGroupResponse]
    """

    kwargs = _get_kwargs(
        group_id=group_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    group_id: UUID,
    *,
    client: AuthenticatedClient,
    body: WorkflowTagGroupUpdate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | WorkflowTagGroupResponse | None:
    """Update Tag Group

     Update a workflow tag group.

    Args:
        group_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (WorkflowTagGroupUpdate): Schema for updating a workflow tag group

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | WorkflowTagGroupResponse
    """

    return (
        await asyncio_detailed(
            group_id=group_id,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed

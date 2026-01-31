from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.workflow_response import WorkflowResponse
from ...models.workflow_update import WorkflowUpdate
from ...types import UNSET, Response, Unset


def _get_kwargs(
    workflow_id: UUID,
    *,
    body: WorkflowUpdate,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v1/workflows/{workflow_id}".format(
            workflow_id=quote(str(workflow_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | WorkflowResponse | None:
    if response.status_code == 200:
        response_200 = WorkflowResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | WorkflowResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    workflow_id: UUID,
    *,
    client: AuthenticatedClient,
    body: WorkflowUpdate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | WorkflowResponse]:
    """Update Workflow

     Update a workflow's prompts.

    The current version will be saved to the version history.
    Only the fields provided in the request body will be updated.
    The workflow must belong to the authenticated organization.

    Args:
        workflow_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (WorkflowUpdate): Schema for updating a workflow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | WorkflowResponse]
    """

    kwargs = _get_kwargs(
        workflow_id=workflow_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workflow_id: UUID,
    *,
    client: AuthenticatedClient,
    body: WorkflowUpdate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | WorkflowResponse | None:
    """Update Workflow

     Update a workflow's prompts.

    The current version will be saved to the version history.
    Only the fields provided in the request body will be updated.
    The workflow must belong to the authenticated organization.

    Args:
        workflow_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (WorkflowUpdate): Schema for updating a workflow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | WorkflowResponse
    """

    return sync_detailed(
        workflow_id=workflow_id,
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    workflow_id: UUID,
    *,
    client: AuthenticatedClient,
    body: WorkflowUpdate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | WorkflowResponse]:
    """Update Workflow

     Update a workflow's prompts.

    The current version will be saved to the version history.
    Only the fields provided in the request body will be updated.
    The workflow must belong to the authenticated organization.

    Args:
        workflow_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (WorkflowUpdate): Schema for updating a workflow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | WorkflowResponse]
    """

    kwargs = _get_kwargs(
        workflow_id=workflow_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workflow_id: UUID,
    *,
    client: AuthenticatedClient,
    body: WorkflowUpdate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | WorkflowResponse | None:
    """Update Workflow

     Update a workflow's prompts.

    The current version will be saved to the version history.
    Only the fields provided in the request body will be updated.
    The workflow must belong to the authenticated organization.

    Args:
        workflow_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (WorkflowUpdate): Schema for updating a workflow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | WorkflowResponse
    """

    return (
        await asyncio_detailed(
            workflow_id=workflow_id,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed

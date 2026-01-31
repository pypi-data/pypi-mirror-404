from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.add_tags_request import AddTagsRequest
from ...models.http_validation_error import HTTPValidationError
from ...models.workflow_tag_response import WorkflowTagResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    workflow_id: UUID,
    *,
    body: AddTagsRequest,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/workflows/{workflow_id}/tags".format(
            workflow_id=quote(str(workflow_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[WorkflowTagResponse] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = WorkflowTagResponse.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[HTTPValidationError | list[WorkflowTagResponse]]:
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
    body: AddTagsRequest,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | list[WorkflowTagResponse]]:
    """Add tags to a workflow

     Add one or more tags to a workflow.

    For tags that belong to a group (mutual exclusivity), adding a new tag from that group
    will automatically remove any existing tag from the same group.

    Args:
        workflow_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (AddTagsRequest): Schema for adding tags to a workflow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[WorkflowTagResponse]]
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
    body: AddTagsRequest,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | list[WorkflowTagResponse] | None:
    """Add tags to a workflow

     Add one or more tags to a workflow.

    For tags that belong to a group (mutual exclusivity), adding a new tag from that group
    will automatically remove any existing tag from the same group.

    Args:
        workflow_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (AddTagsRequest): Schema for adding tags to a workflow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[WorkflowTagResponse]
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
    body: AddTagsRequest,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | list[WorkflowTagResponse]]:
    """Add tags to a workflow

     Add one or more tags to a workflow.

    For tags that belong to a group (mutual exclusivity), adding a new tag from that group
    will automatically remove any existing tag from the same group.

    Args:
        workflow_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (AddTagsRequest): Schema for adding tags to a workflow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[WorkflowTagResponse]]
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
    body: AddTagsRequest,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | list[WorkflowTagResponse] | None:
    """Add tags to a workflow

     Add one or more tags to a workflow.

    For tags that belong to a group (mutual exclusivity), adding a new tag from that group
    will automatically remove any existing tag from the same group.

    Args:
        workflow_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (AddTagsRequest): Schema for adding tags to a workflow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[WorkflowTagResponse]
    """

    return (
        await asyncio_detailed(
            workflow_id=workflow_id,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed

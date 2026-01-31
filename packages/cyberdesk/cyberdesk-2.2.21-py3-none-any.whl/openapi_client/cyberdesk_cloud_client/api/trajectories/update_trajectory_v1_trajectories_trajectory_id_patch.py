from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.trajectory_response import TrajectoryResponse
from ...models.trajectory_update import TrajectoryUpdate
from ...types import UNSET, Response, Unset


def _get_kwargs(
    trajectory_id: UUID,
    *,
    body: TrajectoryUpdate,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v1/trajectories/{trajectory_id}".format(
            trajectory_id=quote(str(trajectory_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TrajectoryResponse | None:
    if response.status_code == 200:
        response_200 = TrajectoryResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TrajectoryResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    trajectory_id: UUID,
    *,
    client: AuthenticatedClient,
    body: TrajectoryUpdate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | TrajectoryResponse]:
    """Update Trajectory

     Update a trajectory's data.

    Only the fields provided in the request body will be updated.
    The trajectory must belong to the authenticated organization.

    Args:
        trajectory_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (TrajectoryUpdate): Schema for updating a trajectory

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TrajectoryResponse]
    """

    kwargs = _get_kwargs(
        trajectory_id=trajectory_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    trajectory_id: UUID,
    *,
    client: AuthenticatedClient,
    body: TrajectoryUpdate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | TrajectoryResponse | None:
    """Update Trajectory

     Update a trajectory's data.

    Only the fields provided in the request body will be updated.
    The trajectory must belong to the authenticated organization.

    Args:
        trajectory_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (TrajectoryUpdate): Schema for updating a trajectory

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TrajectoryResponse
    """

    return sync_detailed(
        trajectory_id=trajectory_id,
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    trajectory_id: UUID,
    *,
    client: AuthenticatedClient,
    body: TrajectoryUpdate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | TrajectoryResponse]:
    """Update Trajectory

     Update a trajectory's data.

    Only the fields provided in the request body will be updated.
    The trajectory must belong to the authenticated organization.

    Args:
        trajectory_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (TrajectoryUpdate): Schema for updating a trajectory

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TrajectoryResponse]
    """

    kwargs = _get_kwargs(
        trajectory_id=trajectory_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    trajectory_id: UUID,
    *,
    client: AuthenticatedClient,
    body: TrajectoryUpdate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | TrajectoryResponse | None:
    """Update Trajectory

     Update a trajectory's data.

    Only the fields provided in the request body will be updated.
    The trajectory must belong to the authenticated organization.

    Args:
        trajectory_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (TrajectoryUpdate): Schema for updating a trajectory

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TrajectoryResponse
    """

    return (
        await asyncio_detailed(
            trajectory_id=trajectory_id,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed

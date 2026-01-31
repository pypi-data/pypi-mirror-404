from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.trajectory_response import TrajectoryResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    trajectory_id: UUID,
    *,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/trajectories/{trajectory_id}/duplicate".format(
            trajectory_id=quote(str(trajectory_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TrajectoryResponse | None:
    if response.status_code == 201:
        response_201 = TrajectoryResponse.from_dict(response.json())

        return response_201

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
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | TrajectoryResponse]:
    r"""Duplicate Trajectory

     Duplicate a trajectory with fresh copies of all images.

    Creates a new trajectory with the same data as the source, but with
    all images copied to new paths in storage (copy-on-write semantics).
    The new trajectory starts unapproved and gets a name like \"Original Name (Copy)\".

    Args:
        trajectory_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TrajectoryResponse]
    """

    kwargs = _get_kwargs(
        trajectory_id=trajectory_id,
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
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | TrajectoryResponse | None:
    r"""Duplicate Trajectory

     Duplicate a trajectory with fresh copies of all images.

    Creates a new trajectory with the same data as the source, but with
    all images copied to new paths in storage (copy-on-write semantics).
    The new trajectory starts unapproved and gets a name like \"Original Name (Copy)\".

    Args:
        trajectory_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TrajectoryResponse
    """

    return sync_detailed(
        trajectory_id=trajectory_id,
        client=client,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    trajectory_id: UUID,
    *,
    client: AuthenticatedClient,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | TrajectoryResponse]:
    r"""Duplicate Trajectory

     Duplicate a trajectory with fresh copies of all images.

    Creates a new trajectory with the same data as the source, but with
    all images copied to new paths in storage (copy-on-write semantics).
    The new trajectory starts unapproved and gets a name like \"Original Name (Copy)\".

    Args:
        trajectory_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TrajectoryResponse]
    """

    kwargs = _get_kwargs(
        trajectory_id=trajectory_id,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    trajectory_id: UUID,
    *,
    client: AuthenticatedClient,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | TrajectoryResponse | None:
    r"""Duplicate Trajectory

     Duplicate a trajectory with fresh copies of all images.

    Creates a new trajectory with the same data as the source, but with
    all images copied to new paths in storage (copy-on-write semantics).
    The new trajectory starts unapproved and gets a name like \"Original Name (Copy)\".

    Args:
        trajectory_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.

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
            idempotency_key=idempotency_key,
        )
    ).parsed

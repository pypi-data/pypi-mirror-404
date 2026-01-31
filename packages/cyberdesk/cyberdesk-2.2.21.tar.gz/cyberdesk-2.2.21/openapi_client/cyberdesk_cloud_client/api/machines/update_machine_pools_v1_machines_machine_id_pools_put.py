from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.machine_pool_update import MachinePoolUpdate
from ...models.machine_response import MachineResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    machine_id: UUID,
    *,
    body: MachinePoolUpdate,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/v1/machines/{machine_id}/pools".format(
            machine_id=quote(str(machine_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | MachineResponse | None:
    if response.status_code == 200:
        response_200 = MachineResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | MachineResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    machine_id: UUID,
    *,
    client: AuthenticatedClient,
    body: MachinePoolUpdate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | MachineResponse]:
    """Update Machine Pools

     Update a machine's pool assignments.
    This replaces all existing pool assignments with the new ones.

    Args:
        machine_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (MachinePoolUpdate): Schema for updating a machine's pool assignments

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MachineResponse]
    """

    kwargs = _get_kwargs(
        machine_id=machine_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    machine_id: UUID,
    *,
    client: AuthenticatedClient,
    body: MachinePoolUpdate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | MachineResponse | None:
    """Update Machine Pools

     Update a machine's pool assignments.
    This replaces all existing pool assignments with the new ones.

    Args:
        machine_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (MachinePoolUpdate): Schema for updating a machine's pool assignments

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MachineResponse
    """

    return sync_detailed(
        machine_id=machine_id,
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    machine_id: UUID,
    *,
    client: AuthenticatedClient,
    body: MachinePoolUpdate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | MachineResponse]:
    """Update Machine Pools

     Update a machine's pool assignments.
    This replaces all existing pool assignments with the new ones.

    Args:
        machine_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (MachinePoolUpdate): Schema for updating a machine's pool assignments

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MachineResponse]
    """

    kwargs = _get_kwargs(
        machine_id=machine_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    machine_id: UUID,
    *,
    client: AuthenticatedClient,
    body: MachinePoolUpdate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | MachineResponse | None:
    """Update Machine Pools

     Update a machine's pool assignments.
    This replaces all existing pool assignments with the new ones.

    Args:
        machine_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (MachinePoolUpdate): Schema for updating a machine's pool assignments

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MachineResponse
    """

    return (
        await asyncio_detailed(
            machine_id=machine_id,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed

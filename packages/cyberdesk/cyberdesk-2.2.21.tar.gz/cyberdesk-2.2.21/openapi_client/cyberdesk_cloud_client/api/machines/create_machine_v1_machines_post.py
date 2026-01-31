from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.machine_create import MachineCreate
from ...models.machine_response import MachineResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: MachineCreate,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/machines",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | MachineResponse | None:
    if response.status_code == 201:
        response_201 = MachineResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | MachineResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: MachineCreate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | MachineResponse]:
    """Create Machine

     Create a new machine.

    The machine will be associated with the authenticated organization.

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (MachineCreate): Schema for creating a machine

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MachineResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: MachineCreate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | MachineResponse | None:
    """Create Machine

     Create a new machine.

    The machine will be associated with the authenticated organization.

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (MachineCreate): Schema for creating a machine

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MachineResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: MachineCreate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | MachineResponse]:
    """Create Machine

     Create a new machine.

    The machine will be associated with the authenticated organization.

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (MachineCreate): Schema for creating a machine

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MachineResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: MachineCreate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | MachineResponse | None:
    """Create Machine

     Create a new machine.

    The machine will be associated with the authenticated organization.

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (MachineCreate): Schema for creating a machine

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MachineResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed

from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.connection_create import ConnectionCreate
from ...models.connection_response import ConnectionResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    connection_id: UUID,
    *,
    body: ConnectionCreate,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v1/connections/{connection_id}".format(
            connection_id=quote(str(connection_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ConnectionResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = ConnectionResponse.from_dict(response.json())

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
) -> Response[ConnectionResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    connection_id: UUID,
    *,
    client: AuthenticatedClient,
    body: ConnectionCreate,
    idempotency_key: str | Unset = UNSET,
) -> Response[ConnectionResponse | HTTPValidationError]:
    """Update Connection

     Update a connection's status or timestamps.

    Only the fields provided in the request body will be updated.
    The connection must belong to a machine owned by the authenticated organization.

    Args:
        connection_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (ConnectionCreate): Schema for creating a connection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ConnectionResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        connection_id=connection_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    connection_id: UUID,
    *,
    client: AuthenticatedClient,
    body: ConnectionCreate,
    idempotency_key: str | Unset = UNSET,
) -> ConnectionResponse | HTTPValidationError | None:
    """Update Connection

     Update a connection's status or timestamps.

    Only the fields provided in the request body will be updated.
    The connection must belong to a machine owned by the authenticated organization.

    Args:
        connection_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (ConnectionCreate): Schema for creating a connection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ConnectionResponse | HTTPValidationError
    """

    return sync_detailed(
        connection_id=connection_id,
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    connection_id: UUID,
    *,
    client: AuthenticatedClient,
    body: ConnectionCreate,
    idempotency_key: str | Unset = UNSET,
) -> Response[ConnectionResponse | HTTPValidationError]:
    """Update Connection

     Update a connection's status or timestamps.

    Only the fields provided in the request body will be updated.
    The connection must belong to a machine owned by the authenticated organization.

    Args:
        connection_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (ConnectionCreate): Schema for creating a connection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ConnectionResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        connection_id=connection_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    connection_id: UUID,
    *,
    client: AuthenticatedClient,
    body: ConnectionCreate,
    idempotency_key: str | Unset = UNSET,
) -> ConnectionResponse | HTTPValidationError | None:
    """Update Connection

     Update a connection's status or timestamps.

    Only the fields provided in the request body will be updated.
    The connection must belong to a machine owned by the authenticated organization.

    Args:
        connection_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (ConnectionCreate): Schema for creating a connection

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ConnectionResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            connection_id=connection_id,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed

from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.pool_response import PoolResponse
from ...models.pool_update import PoolUpdate
from ...types import UNSET, Response, Unset


def _get_kwargs(
    pool_id: UUID,
    *,
    body: PoolUpdate,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v1/pools/{pool_id}".format(
            pool_id=quote(str(pool_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | PoolResponse | None:
    if response.status_code == 200:
        response_200 = PoolResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | PoolResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    pool_id: UUID,
    *,
    client: AuthenticatedClient,
    body: PoolUpdate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | PoolResponse]:
    """Update Pool

     Update a pool's details.

    Args:
        pool_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (PoolUpdate): Schema for updating a pool

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PoolResponse]
    """

    kwargs = _get_kwargs(
        pool_id=pool_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    pool_id: UUID,
    *,
    client: AuthenticatedClient,
    body: PoolUpdate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | PoolResponse | None:
    """Update Pool

     Update a pool's details.

    Args:
        pool_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (PoolUpdate): Schema for updating a pool

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PoolResponse
    """

    return sync_detailed(
        pool_id=pool_id,
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    pool_id: UUID,
    *,
    client: AuthenticatedClient,
    body: PoolUpdate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | PoolResponse]:
    """Update Pool

     Update a pool's details.

    Args:
        pool_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (PoolUpdate): Schema for updating a pool

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PoolResponse]
    """

    kwargs = _get_kwargs(
        pool_id=pool_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    pool_id: UUID,
    *,
    client: AuthenticatedClient,
    body: PoolUpdate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | PoolResponse | None:
    """Update Pool

     Update a pool's details.

    Args:
        pool_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (PoolUpdate): Schema for updating a pool

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PoolResponse
    """

    return (
        await asyncio_detailed(
            pool_id=pool_id,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed

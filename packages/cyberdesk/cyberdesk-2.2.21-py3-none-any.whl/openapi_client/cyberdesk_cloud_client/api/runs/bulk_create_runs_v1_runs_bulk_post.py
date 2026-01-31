from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.run_bulk_create import RunBulkCreate
from ...models.run_bulk_create_response import RunBulkCreateResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: RunBulkCreate,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/runs/bulk",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | RunBulkCreateResponse | None:
    if response.status_code == 201:
        response_201 = RunBulkCreateResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | RunBulkCreateResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: RunBulkCreate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | RunBulkCreateResponse]:
    """Bulk Create Runs

     Create multiple runs with the same configuration.

    This endpoint creates multiple runs efficiently:
    - All runs are created in a single database transaction
    - Temporal workflows are started asynchronously
    - Returns immediately with created run details

    Maximum 1000 runs can be created in a single request.

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (RunBulkCreate): Schema for bulk creating runs

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RunBulkCreateResponse]
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
    body: RunBulkCreate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | RunBulkCreateResponse | None:
    """Bulk Create Runs

     Create multiple runs with the same configuration.

    This endpoint creates multiple runs efficiently:
    - All runs are created in a single database transaction
    - Temporal workflows are started asynchronously
    - Returns immediately with created run details

    Maximum 1000 runs can be created in a single request.

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (RunBulkCreate): Schema for bulk creating runs

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RunBulkCreateResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: RunBulkCreate,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | RunBulkCreateResponse]:
    """Bulk Create Runs

     Create multiple runs with the same configuration.

    This endpoint creates multiple runs efficiently:
    - All runs are created in a single database transaction
    - Temporal workflows are started asynchronously
    - Returns immediately with created run details

    Maximum 1000 runs can be created in a single request.

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (RunBulkCreate): Schema for bulk creating runs

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RunBulkCreateResponse]
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
    body: RunBulkCreate,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | RunBulkCreateResponse | None:
    """Bulk Create Runs

     Create multiple runs with the same configuration.

    This endpoint creates multiple runs efficiently:
    - All runs are created in a single database transaction
    - Temporal workflows are started asynchronously
    - Returns immediately with created run details

    Maximum 1000 runs can be created in a single request.

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (RunBulkCreate): Schema for bulk creating runs

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RunBulkCreateResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed

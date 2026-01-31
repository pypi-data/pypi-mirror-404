from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.health_check_v1_health_get_response_health_check_v1_health_get import (
    HealthCheckV1HealthGetResponseHealthCheckV1HealthGet,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/health",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HealthCheckV1HealthGetResponseHealthCheckV1HealthGet | None:
    if response.status_code == 200:
        response_200 = HealthCheckV1HealthGetResponseHealthCheckV1HealthGet.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HealthCheckV1HealthGetResponseHealthCheckV1HealthGet]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[HealthCheckV1HealthGetResponseHealthCheckV1HealthGet]:
    """Health Check

     Basic health check endpoint.

    Returns the service status without authentication.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HealthCheckV1HealthGetResponseHealthCheckV1HealthGet]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> HealthCheckV1HealthGetResponseHealthCheckV1HealthGet | None:
    """Health Check

     Basic health check endpoint.

    Returns the service status without authentication.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HealthCheckV1HealthGetResponseHealthCheckV1HealthGet
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[HealthCheckV1HealthGetResponseHealthCheckV1HealthGet]:
    """Health Check

     Basic health check endpoint.

    Returns the service status without authentication.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HealthCheckV1HealthGetResponseHealthCheckV1HealthGet]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> HealthCheckV1HealthGetResponseHealthCheckV1HealthGet | None:
    """Health Check

     Basic health check endpoint.

    Returns the service status without authentication.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HealthCheckV1HealthGetResponseHealthCheckV1HealthGet
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed

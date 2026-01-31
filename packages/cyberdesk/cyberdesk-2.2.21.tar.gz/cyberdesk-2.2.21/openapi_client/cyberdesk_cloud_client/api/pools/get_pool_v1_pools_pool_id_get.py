from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.pool_response_with_includes import PoolResponseWithIncludes
from ...types import UNSET, Response, Unset


def _get_kwargs(
    pool_id: UUID,
    *,
    include_machines: bool | Unset = False,
    include: None | str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["include_machines"] = include_machines

    json_include: None | str | Unset
    if isinstance(include, Unset):
        json_include = UNSET
    else:
        json_include = include
    params["include"] = json_include

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/pools/{pool_id}".format(
            pool_id=quote(str(pool_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | PoolResponseWithIncludes | None:
    if response.status_code == 200:
        response_200 = PoolResponseWithIncludes.from_dict(response.json())

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
) -> Response[HTTPValidationError | PoolResponseWithIncludes]:
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
    include_machines: bool | Unset = False,
    include: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | PoolResponseWithIncludes]:
    """Get Pool

     Get a specific pool by ID.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Note: The `include_machines` parameter is deprecated. Use `include=machines` instead.

    Args:
        pool_id (UUID):
        include_machines (bool | Unset): [Deprecated] Use include=machines instead. Include full
            machine details Default: False.
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: machines. Example: include=machines

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PoolResponseWithIncludes]
    """

    kwargs = _get_kwargs(
        pool_id=pool_id,
        include_machines=include_machines,
        include=include,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    pool_id: UUID,
    *,
    client: AuthenticatedClient,
    include_machines: bool | Unset = False,
    include: None | str | Unset = UNSET,
) -> HTTPValidationError | PoolResponseWithIncludes | None:
    """Get Pool

     Get a specific pool by ID.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Note: The `include_machines` parameter is deprecated. Use `include=machines` instead.

    Args:
        pool_id (UUID):
        include_machines (bool | Unset): [Deprecated] Use include=machines instead. Include full
            machine details Default: False.
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: machines. Example: include=machines

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PoolResponseWithIncludes
    """

    return sync_detailed(
        pool_id=pool_id,
        client=client,
        include_machines=include_machines,
        include=include,
    ).parsed


async def asyncio_detailed(
    pool_id: UUID,
    *,
    client: AuthenticatedClient,
    include_machines: bool | Unset = False,
    include: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | PoolResponseWithIncludes]:
    """Get Pool

     Get a specific pool by ID.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Note: The `include_machines` parameter is deprecated. Use `include=machines` instead.

    Args:
        pool_id (UUID):
        include_machines (bool | Unset): [Deprecated] Use include=machines instead. Include full
            machine details Default: False.
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: machines. Example: include=machines

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PoolResponseWithIncludes]
    """

    kwargs = _get_kwargs(
        pool_id=pool_id,
        include_machines=include_machines,
        include=include,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    pool_id: UUID,
    *,
    client: AuthenticatedClient,
    include_machines: bool | Unset = False,
    include: None | str | Unset = UNSET,
) -> HTTPValidationError | PoolResponseWithIncludes | None:
    """Get Pool

     Get a specific pool by ID.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Note: The `include_machines` parameter is deprecated. Use `include=machines` instead.

    Args:
        pool_id (UUID):
        include_machines (bool | Unset): [Deprecated] Use include=machines instead. Include full
            machine details Default: False.
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: machines. Example: include=machines

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PoolResponseWithIncludes
    """

    return (
        await asyncio_detailed(
            pool_id=pool_id,
            client=client,
            include_machines=include_machines,
            include=include,
        )
    ).parsed

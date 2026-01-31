import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.machine_status import MachineStatus
from ...models.paginated_response_with_includes_machine_response import PaginatedResponseWithIncludesMachineResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    search: None | str | Unset = UNSET,
    status: MachineStatus | None | Unset = UNSET,
    created_at_from: datetime.datetime | None | Unset = UNSET,
    created_at_to: datetime.datetime | None | Unset = UNSET,
    include: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_search: None | str | Unset
    if isinstance(search, Unset):
        json_search = UNSET
    else:
        json_search = search
    params["search"] = json_search

    json_status: None | str | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    elif isinstance(status, MachineStatus):
        json_status = status.value
    else:
        json_status = status
    params["status"] = json_status

    json_created_at_from: None | str | Unset
    if isinstance(created_at_from, Unset):
        json_created_at_from = UNSET
    elif isinstance(created_at_from, datetime.datetime):
        json_created_at_from = created_at_from.isoformat()
    else:
        json_created_at_from = created_at_from
    params["created_at_from"] = json_created_at_from

    json_created_at_to: None | str | Unset
    if isinstance(created_at_to, Unset):
        json_created_at_to = UNSET
    elif isinstance(created_at_to, datetime.datetime):
        json_created_at_to = created_at_to.isoformat()
    else:
        json_created_at_to = created_at_to
    params["created_at_to"] = json_created_at_to

    json_include: None | str | Unset
    if isinstance(include, Unset):
        json_include = UNSET
    else:
        json_include = include
    params["include"] = json_include

    params["skip"] = skip

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/machines",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | PaginatedResponseWithIncludesMachineResponse | None:
    if response.status_code == 200:
        response_200 = PaginatedResponseWithIncludesMachineResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | PaginatedResponseWithIncludesMachineResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    search: None | str | Unset = UNSET,
    status: MachineStatus | None | Unset = UNSET,
    created_at_from: datetime.datetime | None | Unset = UNSET,
    created_at_to: datetime.datetime | None | Unset = UNSET,
    include: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> Response[HTTPValidationError | PaginatedResponseWithIncludesMachineResponse]:
    """List Machines

     List all machines for the authenticated organization.

    Supports pagination and filtering by status.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        search (None | str | Unset): Search machines by name or hostname (case-insensitive
            substring match)
        status (MachineStatus | None | Unset): Filter by machine status
        created_at_from (datetime.datetime | None | Unset): Filter machines created at or after
            this ISO timestamp (UTC)
        created_at_to (datetime.datetime | None | Unset): Filter machines created at or before
            this ISO timestamp (UTC)
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: pools. Example: include=pools
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PaginatedResponseWithIncludesMachineResponse]
    """

    kwargs = _get_kwargs(
        search=search,
        status=status,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        include=include,
        skip=skip,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    search: None | str | Unset = UNSET,
    status: MachineStatus | None | Unset = UNSET,
    created_at_from: datetime.datetime | None | Unset = UNSET,
    created_at_to: datetime.datetime | None | Unset = UNSET,
    include: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> HTTPValidationError | PaginatedResponseWithIncludesMachineResponse | None:
    """List Machines

     List all machines for the authenticated organization.

    Supports pagination and filtering by status.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        search (None | str | Unset): Search machines by name or hostname (case-insensitive
            substring match)
        status (MachineStatus | None | Unset): Filter by machine status
        created_at_from (datetime.datetime | None | Unset): Filter machines created at or after
            this ISO timestamp (UTC)
        created_at_to (datetime.datetime | None | Unset): Filter machines created at or before
            this ISO timestamp (UTC)
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: pools. Example: include=pools
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PaginatedResponseWithIncludesMachineResponse
    """

    return sync_detailed(
        client=client,
        search=search,
        status=status,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        include=include,
        skip=skip,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    search: None | str | Unset = UNSET,
    status: MachineStatus | None | Unset = UNSET,
    created_at_from: datetime.datetime | None | Unset = UNSET,
    created_at_to: datetime.datetime | None | Unset = UNSET,
    include: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> Response[HTTPValidationError | PaginatedResponseWithIncludesMachineResponse]:
    """List Machines

     List all machines for the authenticated organization.

    Supports pagination and filtering by status.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        search (None | str | Unset): Search machines by name or hostname (case-insensitive
            substring match)
        status (MachineStatus | None | Unset): Filter by machine status
        created_at_from (datetime.datetime | None | Unset): Filter machines created at or after
            this ISO timestamp (UTC)
        created_at_to (datetime.datetime | None | Unset): Filter machines created at or before
            this ISO timestamp (UTC)
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: pools. Example: include=pools
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PaginatedResponseWithIncludesMachineResponse]
    """

    kwargs = _get_kwargs(
        search=search,
        status=status,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        include=include,
        skip=skip,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    search: None | str | Unset = UNSET,
    status: MachineStatus | None | Unset = UNSET,
    created_at_from: datetime.datetime | None | Unset = UNSET,
    created_at_to: datetime.datetime | None | Unset = UNSET,
    include: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> HTTPValidationError | PaginatedResponseWithIncludesMachineResponse | None:
    """List Machines

     List all machines for the authenticated organization.

    Supports pagination and filtering by status.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        search (None | str | Unset): Search machines by name or hostname (case-insensitive
            substring match)
        status (MachineStatus | None | Unset): Filter by machine status
        created_at_from (datetime.datetime | None | Unset): Filter machines created at or after
            this ISO timestamp (UTC)
        created_at_to (datetime.datetime | None | Unset): Filter machines created at or before
            this ISO timestamp (UTC)
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: pools. Example: include=pools
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PaginatedResponseWithIncludesMachineResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            search=search,
            status=status,
            created_at_from=created_at_from,
            created_at_to=created_at_to,
            include=include,
            skip=skip,
            limit=limit,
        )
    ).parsed

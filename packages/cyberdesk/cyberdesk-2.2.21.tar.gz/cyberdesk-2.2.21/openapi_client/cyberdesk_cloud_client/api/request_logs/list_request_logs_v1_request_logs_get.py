from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.paginated_response import PaginatedResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    machine_id: None | Unset | UUID = UNSET,
    method: None | str | Unset = UNSET,
    status_code: int | None | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_machine_id: None | str | Unset
    if isinstance(machine_id, Unset):
        json_machine_id = UNSET
    elif isinstance(machine_id, UUID):
        json_machine_id = str(machine_id)
    else:
        json_machine_id = machine_id
    params["machine_id"] = json_machine_id

    json_method: None | str | Unset
    if isinstance(method, Unset):
        json_method = UNSET
    else:
        json_method = method
    params["method"] = json_method

    json_status_code: int | None | Unset
    if isinstance(status_code, Unset):
        json_status_code = UNSET
    else:
        json_status_code = status_code
    params["status_code"] = json_status_code

    params["skip"] = skip

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/request-logs",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | PaginatedResponse | None:
    if response.status_code == 200:
        response_200 = PaginatedResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | PaginatedResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    machine_id: None | Unset | UUID = UNSET,
    method: None | str | Unset = UNSET,
    status_code: int | None | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> Response[HTTPValidationError | PaginatedResponse]:
    """List Request Logs

     List all request logs for the authenticated organization's machines.

    Supports pagination and filtering by machine, HTTP method, and status code.

    Args:
        machine_id (None | Unset | UUID): Filter by machine ID
        method (None | str | Unset): Filter by HTTP method
        status_code (int | None | Unset): Filter by status code
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PaginatedResponse]
    """

    kwargs = _get_kwargs(
        machine_id=machine_id,
        method=method,
        status_code=status_code,
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
    machine_id: None | Unset | UUID = UNSET,
    method: None | str | Unset = UNSET,
    status_code: int | None | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> HTTPValidationError | PaginatedResponse | None:
    """List Request Logs

     List all request logs for the authenticated organization's machines.

    Supports pagination and filtering by machine, HTTP method, and status code.

    Args:
        machine_id (None | Unset | UUID): Filter by machine ID
        method (None | str | Unset): Filter by HTTP method
        status_code (int | None | Unset): Filter by status code
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PaginatedResponse
    """

    return sync_detailed(
        client=client,
        machine_id=machine_id,
        method=method,
        status_code=status_code,
        skip=skip,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    machine_id: None | Unset | UUID = UNSET,
    method: None | str | Unset = UNSET,
    status_code: int | None | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> Response[HTTPValidationError | PaginatedResponse]:
    """List Request Logs

     List all request logs for the authenticated organization's machines.

    Supports pagination and filtering by machine, HTTP method, and status code.

    Args:
        machine_id (None | Unset | UUID): Filter by machine ID
        method (None | str | Unset): Filter by HTTP method
        status_code (int | None | Unset): Filter by status code
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PaginatedResponse]
    """

    kwargs = _get_kwargs(
        machine_id=machine_id,
        method=method,
        status_code=status_code,
        skip=skip,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    machine_id: None | Unset | UUID = UNSET,
    method: None | str | Unset = UNSET,
    status_code: int | None | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> HTTPValidationError | PaginatedResponse | None:
    """List Request Logs

     List all request logs for the authenticated organization's machines.

    Supports pagination and filtering by machine, HTTP method, and status code.

    Args:
        machine_id (None | Unset | UUID): Filter by machine ID
        method (None | str | Unset): Filter by HTTP method
        status_code (int | None | Unset): Filter by status code
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PaginatedResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            machine_id=machine_id,
            method=method,
            status_code=status_code,
            skip=skip,
            limit=limit,
        )
    ).parsed

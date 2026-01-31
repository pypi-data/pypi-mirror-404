from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.machine_response_with_includes import MachineResponseWithIncludes
from ...types import UNSET, Response, Unset


def _get_kwargs(
    machine_id: UUID,
    *,
    include: None | str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_include: None | str | Unset
    if isinstance(include, Unset):
        json_include = UNSET
    else:
        json_include = include
    params["include"] = json_include

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/machines/{machine_id}".format(
            machine_id=quote(str(machine_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | MachineResponseWithIncludes | None:
    if response.status_code == 200:
        response_200 = MachineResponseWithIncludes.from_dict(response.json())

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
) -> Response[HTTPValidationError | MachineResponseWithIncludes]:
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
    include: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | MachineResponseWithIncludes]:
    """Get Machine

     Get a specific machine by ID.

    The machine must belong to the authenticated organization.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        machine_id (UUID):
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: pools. Example: include=pools

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MachineResponseWithIncludes]
    """

    kwargs = _get_kwargs(
        machine_id=machine_id,
        include=include,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    machine_id: UUID,
    *,
    client: AuthenticatedClient,
    include: None | str | Unset = UNSET,
) -> HTTPValidationError | MachineResponseWithIncludes | None:
    """Get Machine

     Get a specific machine by ID.

    The machine must belong to the authenticated organization.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        machine_id (UUID):
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: pools. Example: include=pools

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MachineResponseWithIncludes
    """

    return sync_detailed(
        machine_id=machine_id,
        client=client,
        include=include,
    ).parsed


async def asyncio_detailed(
    machine_id: UUID,
    *,
    client: AuthenticatedClient,
    include: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | MachineResponseWithIncludes]:
    """Get Machine

     Get a specific machine by ID.

    The machine must belong to the authenticated organization.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        machine_id (UUID):
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: pools. Example: include=pools

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MachineResponseWithIncludes]
    """

    kwargs = _get_kwargs(
        machine_id=machine_id,
        include=include,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    machine_id: UUID,
    *,
    client: AuthenticatedClient,
    include: None | str | Unset = UNSET,
) -> HTTPValidationError | MachineResponseWithIncludes | None:
    """Get Machine

     Get a specific machine by ID.

    The machine must belong to the authenticated organization.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        machine_id (UUID):
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: pools. Example: include=pools

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MachineResponseWithIncludes
    """

    return (
        await asyncio_detailed(
            machine_id=machine_id,
            client=client,
            include=include,
        )
    ).parsed

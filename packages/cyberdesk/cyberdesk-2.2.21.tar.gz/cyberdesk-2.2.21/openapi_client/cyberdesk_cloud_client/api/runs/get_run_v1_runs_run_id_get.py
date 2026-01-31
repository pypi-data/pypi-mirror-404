from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.run_response_with_includes import RunResponseWithIncludes
from ...types import UNSET, Response, Unset


def _get_kwargs(
    run_id: UUID,
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
        "url": "/v1/runs/{run_id}".format(
            run_id=quote(str(run_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | RunResponseWithIncludes | None:
    if response.status_code == 200:
        response_200 = RunResponseWithIncludes.from_dict(response.json())

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
) -> Response[HTTPValidationError | RunResponseWithIncludes]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    run_id: UUID,
    *,
    client: AuthenticatedClient,
    include: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | RunResponseWithIncludes]:
    """Get Run

     Get a specific run by ID.

    The run must belong to the authenticated organization.
    Returns the run with its associated workflow and machine data.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        run_id (UUID):
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow, machine, machine.pools. Example: include=workflow,machine

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RunResponseWithIncludes]
    """

    kwargs = _get_kwargs(
        run_id=run_id,
        include=include,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    run_id: UUID,
    *,
    client: AuthenticatedClient,
    include: None | str | Unset = UNSET,
) -> HTTPValidationError | RunResponseWithIncludes | None:
    """Get Run

     Get a specific run by ID.

    The run must belong to the authenticated organization.
    Returns the run with its associated workflow and machine data.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        run_id (UUID):
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow, machine, machine.pools. Example: include=workflow,machine

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RunResponseWithIncludes
    """

    return sync_detailed(
        run_id=run_id,
        client=client,
        include=include,
    ).parsed


async def asyncio_detailed(
    run_id: UUID,
    *,
    client: AuthenticatedClient,
    include: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | RunResponseWithIncludes]:
    """Get Run

     Get a specific run by ID.

    The run must belong to the authenticated organization.
    Returns the run with its associated workflow and machine data.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        run_id (UUID):
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow, machine, machine.pools. Example: include=workflow,machine

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RunResponseWithIncludes]
    """

    kwargs = _get_kwargs(
        run_id=run_id,
        include=include,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    run_id: UUID,
    *,
    client: AuthenticatedClient,
    include: None | str | Unset = UNSET,
) -> HTTPValidationError | RunResponseWithIncludes | None:
    """Get Run

     Get a specific run by ID.

    The run must belong to the authenticated organization.
    Returns the run with its associated workflow and machine data.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        run_id (UUID):
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow, machine, machine.pools. Example: include=workflow,machine

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RunResponseWithIncludes
    """

    return (
        await asyncio_detailed(
            run_id=run_id,
            client=client,
            include=include,
        )
    ).parsed

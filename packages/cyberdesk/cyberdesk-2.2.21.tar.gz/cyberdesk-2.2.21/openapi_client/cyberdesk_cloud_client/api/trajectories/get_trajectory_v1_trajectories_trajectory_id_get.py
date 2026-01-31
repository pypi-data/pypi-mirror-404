from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.trajectory_response_with_includes import TrajectoryResponseWithIncludes
from ...types import UNSET, Response, Unset


def _get_kwargs(
    trajectory_id: UUID,
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
        "url": "/v1/trajectories/{trajectory_id}".format(
            trajectory_id=quote(str(trajectory_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TrajectoryResponseWithIncludes | None:
    if response.status_code == 200:
        response_200 = TrajectoryResponseWithIncludes.from_dict(response.json())

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
) -> Response[HTTPValidationError | TrajectoryResponseWithIncludes]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    trajectory_id: UUID,
    *,
    client: AuthenticatedClient,
    include: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | TrajectoryResponseWithIncludes]:
    """Get Trajectory

     Get a specific trajectory by ID.

    The trajectory must belong to the authenticated organization.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Example: `?include=workflow` to include the associated workflow data.

    Args:
        trajectory_id (UUID):
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow. Example: include=workflow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TrajectoryResponseWithIncludes]
    """

    kwargs = _get_kwargs(
        trajectory_id=trajectory_id,
        include=include,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    trajectory_id: UUID,
    *,
    client: AuthenticatedClient,
    include: None | str | Unset = UNSET,
) -> HTTPValidationError | TrajectoryResponseWithIncludes | None:
    """Get Trajectory

     Get a specific trajectory by ID.

    The trajectory must belong to the authenticated organization.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Example: `?include=workflow` to include the associated workflow data.

    Args:
        trajectory_id (UUID):
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow. Example: include=workflow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TrajectoryResponseWithIncludes
    """

    return sync_detailed(
        trajectory_id=trajectory_id,
        client=client,
        include=include,
    ).parsed


async def asyncio_detailed(
    trajectory_id: UUID,
    *,
    client: AuthenticatedClient,
    include: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | TrajectoryResponseWithIncludes]:
    """Get Trajectory

     Get a specific trajectory by ID.

    The trajectory must belong to the authenticated organization.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Example: `?include=workflow` to include the associated workflow data.

    Args:
        trajectory_id (UUID):
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow. Example: include=workflow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TrajectoryResponseWithIncludes]
    """

    kwargs = _get_kwargs(
        trajectory_id=trajectory_id,
        include=include,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    trajectory_id: UUID,
    *,
    client: AuthenticatedClient,
    include: None | str | Unset = UNSET,
) -> HTTPValidationError | TrajectoryResponseWithIncludes | None:
    """Get Trajectory

     Get a specific trajectory by ID.

    The trajectory must belong to the authenticated organization.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Example: `?include=workflow` to include the associated workflow data.

    Args:
        trajectory_id (UUID):
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow. Example: include=workflow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TrajectoryResponseWithIncludes
    """

    return (
        await asyncio_detailed(
            trajectory_id=trajectory_id,
            client=client,
            include=include,
        )
    ).parsed

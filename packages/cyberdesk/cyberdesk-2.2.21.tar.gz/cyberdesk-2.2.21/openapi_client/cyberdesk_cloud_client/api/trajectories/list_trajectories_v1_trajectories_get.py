import datetime
from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.paginated_response_with_includes_trajectory_response import (
    PaginatedResponseWithIncludesTrajectoryResponse,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    search: None | str | Unset = UNSET,
    workflow_id: None | Unset | UUID = UNSET,
    is_approved: bool | None | Unset = UNSET,
    created_at_from: datetime.datetime | None | Unset = UNSET,
    created_at_to: datetime.datetime | None | Unset = UNSET,
    updated_at_from: datetime.datetime | None | Unset = UNSET,
    updated_at_to: datetime.datetime | None | Unset = UNSET,
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

    json_workflow_id: None | str | Unset
    if isinstance(workflow_id, Unset):
        json_workflow_id = UNSET
    elif isinstance(workflow_id, UUID):
        json_workflow_id = str(workflow_id)
    else:
        json_workflow_id = workflow_id
    params["workflow_id"] = json_workflow_id

    json_is_approved: bool | None | Unset
    if isinstance(is_approved, Unset):
        json_is_approved = UNSET
    else:
        json_is_approved = is_approved
    params["is_approved"] = json_is_approved

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

    json_updated_at_from: None | str | Unset
    if isinstance(updated_at_from, Unset):
        json_updated_at_from = UNSET
    elif isinstance(updated_at_from, datetime.datetime):
        json_updated_at_from = updated_at_from.isoformat()
    else:
        json_updated_at_from = updated_at_from
    params["updated_at_from"] = json_updated_at_from

    json_updated_at_to: None | str | Unset
    if isinstance(updated_at_to, Unset):
        json_updated_at_to = UNSET
    elif isinstance(updated_at_to, datetime.datetime):
        json_updated_at_to = updated_at_to.isoformat()
    else:
        json_updated_at_to = updated_at_to
    params["updated_at_to"] = json_updated_at_to

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
        "url": "/v1/trajectories",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | PaginatedResponseWithIncludesTrajectoryResponse | None:
    if response.status_code == 200:
        response_200 = PaginatedResponseWithIncludesTrajectoryResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | PaginatedResponseWithIncludesTrajectoryResponse]:
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
    workflow_id: None | Unset | UUID = UNSET,
    is_approved: bool | None | Unset = UNSET,
    created_at_from: datetime.datetime | None | Unset = UNSET,
    created_at_to: datetime.datetime | None | Unset = UNSET,
    updated_at_from: datetime.datetime | None | Unset = UNSET,
    updated_at_to: datetime.datetime | None | Unset = UNSET,
    include: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> Response[HTTPValidationError | PaginatedResponseWithIncludesTrajectoryResponse]:
    """List Trajectories

     List all trajectories for the authenticated organization.

    Supports pagination and filtering by workflow and approval status.
    Only approved trajectories are used during workflow execution.
    Returns trajectories with their associated workflow data.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        search (None | str | Unset): Search trajectories by name or description (case-insensitive
            substring match)
        workflow_id (None | Unset | UUID): Filter by workflow ID
        is_approved (bool | None | Unset): Filter by approval status (true=approved, false=not
            approved)
        created_at_from (datetime.datetime | None | Unset): Filter trajectories created at or
            after this ISO timestamp (UTC)
        created_at_to (datetime.datetime | None | Unset): Filter trajectories created at or before
            this ISO timestamp (UTC)
        updated_at_from (datetime.datetime | None | Unset): Filter trajectories updated at or
            after this ISO timestamp (UTC)
        updated_at_to (datetime.datetime | None | Unset): Filter trajectories updated at or before
            this ISO timestamp (UTC)
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow. Example: include=workflow
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PaginatedResponseWithIncludesTrajectoryResponse]
    """

    kwargs = _get_kwargs(
        search=search,
        workflow_id=workflow_id,
        is_approved=is_approved,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        updated_at_from=updated_at_from,
        updated_at_to=updated_at_to,
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
    workflow_id: None | Unset | UUID = UNSET,
    is_approved: bool | None | Unset = UNSET,
    created_at_from: datetime.datetime | None | Unset = UNSET,
    created_at_to: datetime.datetime | None | Unset = UNSET,
    updated_at_from: datetime.datetime | None | Unset = UNSET,
    updated_at_to: datetime.datetime | None | Unset = UNSET,
    include: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> HTTPValidationError | PaginatedResponseWithIncludesTrajectoryResponse | None:
    """List Trajectories

     List all trajectories for the authenticated organization.

    Supports pagination and filtering by workflow and approval status.
    Only approved trajectories are used during workflow execution.
    Returns trajectories with their associated workflow data.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        search (None | str | Unset): Search trajectories by name or description (case-insensitive
            substring match)
        workflow_id (None | Unset | UUID): Filter by workflow ID
        is_approved (bool | None | Unset): Filter by approval status (true=approved, false=not
            approved)
        created_at_from (datetime.datetime | None | Unset): Filter trajectories created at or
            after this ISO timestamp (UTC)
        created_at_to (datetime.datetime | None | Unset): Filter trajectories created at or before
            this ISO timestamp (UTC)
        updated_at_from (datetime.datetime | None | Unset): Filter trajectories updated at or
            after this ISO timestamp (UTC)
        updated_at_to (datetime.datetime | None | Unset): Filter trajectories updated at or before
            this ISO timestamp (UTC)
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow. Example: include=workflow
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PaginatedResponseWithIncludesTrajectoryResponse
    """

    return sync_detailed(
        client=client,
        search=search,
        workflow_id=workflow_id,
        is_approved=is_approved,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        updated_at_from=updated_at_from,
        updated_at_to=updated_at_to,
        include=include,
        skip=skip,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    search: None | str | Unset = UNSET,
    workflow_id: None | Unset | UUID = UNSET,
    is_approved: bool | None | Unset = UNSET,
    created_at_from: datetime.datetime | None | Unset = UNSET,
    created_at_to: datetime.datetime | None | Unset = UNSET,
    updated_at_from: datetime.datetime | None | Unset = UNSET,
    updated_at_to: datetime.datetime | None | Unset = UNSET,
    include: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> Response[HTTPValidationError | PaginatedResponseWithIncludesTrajectoryResponse]:
    """List Trajectories

     List all trajectories for the authenticated organization.

    Supports pagination and filtering by workflow and approval status.
    Only approved trajectories are used during workflow execution.
    Returns trajectories with their associated workflow data.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        search (None | str | Unset): Search trajectories by name or description (case-insensitive
            substring match)
        workflow_id (None | Unset | UUID): Filter by workflow ID
        is_approved (bool | None | Unset): Filter by approval status (true=approved, false=not
            approved)
        created_at_from (datetime.datetime | None | Unset): Filter trajectories created at or
            after this ISO timestamp (UTC)
        created_at_to (datetime.datetime | None | Unset): Filter trajectories created at or before
            this ISO timestamp (UTC)
        updated_at_from (datetime.datetime | None | Unset): Filter trajectories updated at or
            after this ISO timestamp (UTC)
        updated_at_to (datetime.datetime | None | Unset): Filter trajectories updated at or before
            this ISO timestamp (UTC)
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow. Example: include=workflow
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PaginatedResponseWithIncludesTrajectoryResponse]
    """

    kwargs = _get_kwargs(
        search=search,
        workflow_id=workflow_id,
        is_approved=is_approved,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        updated_at_from=updated_at_from,
        updated_at_to=updated_at_to,
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
    workflow_id: None | Unset | UUID = UNSET,
    is_approved: bool | None | Unset = UNSET,
    created_at_from: datetime.datetime | None | Unset = UNSET,
    created_at_to: datetime.datetime | None | Unset = UNSET,
    updated_at_from: datetime.datetime | None | Unset = UNSET,
    updated_at_to: datetime.datetime | None | Unset = UNSET,
    include: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> HTTPValidationError | PaginatedResponseWithIncludesTrajectoryResponse | None:
    """List Trajectories

     List all trajectories for the authenticated organization.

    Supports pagination and filtering by workflow and approval status.
    Only approved trajectories are used during workflow execution.
    Returns trajectories with their associated workflow data.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.

    Args:
        search (None | str | Unset): Search trajectories by name or description (case-insensitive
            substring match)
        workflow_id (None | Unset | UUID): Filter by workflow ID
        is_approved (bool | None | Unset): Filter by approval status (true=approved, false=not
            approved)
        created_at_from (datetime.datetime | None | Unset): Filter trajectories created at or
            after this ISO timestamp (UTC)
        created_at_to (datetime.datetime | None | Unset): Filter trajectories created at or before
            this ISO timestamp (UTC)
        updated_at_from (datetime.datetime | None | Unset): Filter trajectories updated at or
            after this ISO timestamp (UTC)
        updated_at_to (datetime.datetime | None | Unset): Filter trajectories updated at or before
            this ISO timestamp (UTC)
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow. Example: include=workflow
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PaginatedResponseWithIncludesTrajectoryResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            search=search,
            workflow_id=workflow_id,
            is_approved=is_approved,
            created_at_from=created_at_from,
            created_at_to=created_at_to,
            updated_at_from=updated_at_from,
            updated_at_to=updated_at_to,
            include=include,
            skip=skip,
            limit=limit,
        )
    ).parsed

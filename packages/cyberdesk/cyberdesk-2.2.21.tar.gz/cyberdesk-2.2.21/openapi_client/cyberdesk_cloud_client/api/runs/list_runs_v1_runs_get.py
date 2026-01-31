import datetime
from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.paginated_response_with_includes_run_response import PaginatedResponseWithIncludesRunResponse
from ...models.run_field import RunField
from ...models.run_status import RunStatus
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    workflow_id: None | Unset | UUID = UNSET,
    machine_id: None | Unset | UUID = UNSET,
    session_id: None | Unset | UUID = UNSET,
    status: None | RunStatus | Unset = UNSET,
    created_at_from: datetime.datetime | None | Unset = UNSET,
    created_at_to: datetime.datetime | None | Unset = UNSET,
    search: None | str | Unset = UNSET,
    deep_search: bool | Unset = False,
    fields: list[RunField] | None | Unset = UNSET,
    include: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_workflow_id: None | str | Unset
    if isinstance(workflow_id, Unset):
        json_workflow_id = UNSET
    elif isinstance(workflow_id, UUID):
        json_workflow_id = str(workflow_id)
    else:
        json_workflow_id = workflow_id
    params["workflow_id"] = json_workflow_id

    json_machine_id: None | str | Unset
    if isinstance(machine_id, Unset):
        json_machine_id = UNSET
    elif isinstance(machine_id, UUID):
        json_machine_id = str(machine_id)
    else:
        json_machine_id = machine_id
    params["machine_id"] = json_machine_id

    json_session_id: None | str | Unset
    if isinstance(session_id, Unset):
        json_session_id = UNSET
    elif isinstance(session_id, UUID):
        json_session_id = str(session_id)
    else:
        json_session_id = session_id
    params["session_id"] = json_session_id

    json_status: None | str | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    elif isinstance(status, RunStatus):
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

    json_search: None | str | Unset
    if isinstance(search, Unset):
        json_search = UNSET
    else:
        json_search = search
    params["search"] = json_search

    params["deep_search"] = deep_search

    json_fields: list[str] | None | Unset
    if isinstance(fields, Unset):
        json_fields = UNSET
    elif isinstance(fields, list):
        json_fields = []
        for fields_type_0_item_data in fields:
            fields_type_0_item = fields_type_0_item_data.value
            json_fields.append(fields_type_0_item)

    else:
        json_fields = fields
    params["fields"] = json_fields

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
        "url": "/v1/runs",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | PaginatedResponseWithIncludesRunResponse | None:
    if response.status_code == 200:
        response_200 = PaginatedResponseWithIncludesRunResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | PaginatedResponseWithIncludesRunResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    workflow_id: None | Unset | UUID = UNSET,
    machine_id: None | Unset | UUID = UNSET,
    session_id: None | Unset | UUID = UNSET,
    status: None | RunStatus | Unset = UNSET,
    created_at_from: datetime.datetime | None | Unset = UNSET,
    created_at_to: datetime.datetime | None | Unset = UNSET,
    search: None | str | Unset = UNSET,
    deep_search: bool | Unset = False,
    fields: list[RunField] | None | Unset = UNSET,
    include: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> Response[HTTPValidationError | PaginatedResponseWithIncludesRunResponse]:
    """List Runs

     List all runs for the authenticated organization.

    Supports pagination and filtering by workflow, machine, and status.
    Returns runs with their associated workflow and machine data.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.
    Resources are deduplicated across all items in the list.

    Args:
        workflow_id (None | Unset | UUID): Filter by workflow ID
        machine_id (None | Unset | UUID): Filter by machine ID
        session_id (None | Unset | UUID): Filter by session ID
        status (None | RunStatus | Unset): Filter by run status
        created_at_from (datetime.datetime | None | Unset): Filter runs created at or after this
            ISO timestamp (UTC)
        created_at_to (datetime.datetime | None | Unset): Filter runs created at or before this
            ISO timestamp (UTC)
        search (None | str | Unset): Search runs by input_values, output_data, error,
            session_alias (case-insensitive substring match)
        deep_search (bool | Unset): If true, also search run_message_history (slower but more
            comprehensive) Default: False.
        fields (list[RunField] | None | Unset): Optional list of fields to include per run. Always
            includes: id, workflow_id, machine_id, status, created_at. Provide multiple 'fields='
            params to include more.
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow, machine, machine.pools. Example: include=workflow,machine
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PaginatedResponseWithIncludesRunResponse]
    """

    kwargs = _get_kwargs(
        workflow_id=workflow_id,
        machine_id=machine_id,
        session_id=session_id,
        status=status,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        search=search,
        deep_search=deep_search,
        fields=fields,
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
    workflow_id: None | Unset | UUID = UNSET,
    machine_id: None | Unset | UUID = UNSET,
    session_id: None | Unset | UUID = UNSET,
    status: None | RunStatus | Unset = UNSET,
    created_at_from: datetime.datetime | None | Unset = UNSET,
    created_at_to: datetime.datetime | None | Unset = UNSET,
    search: None | str | Unset = UNSET,
    deep_search: bool | Unset = False,
    fields: list[RunField] | None | Unset = UNSET,
    include: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> HTTPValidationError | PaginatedResponseWithIncludesRunResponse | None:
    """List Runs

     List all runs for the authenticated organization.

    Supports pagination and filtering by workflow, machine, and status.
    Returns runs with their associated workflow and machine data.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.
    Resources are deduplicated across all items in the list.

    Args:
        workflow_id (None | Unset | UUID): Filter by workflow ID
        machine_id (None | Unset | UUID): Filter by machine ID
        session_id (None | Unset | UUID): Filter by session ID
        status (None | RunStatus | Unset): Filter by run status
        created_at_from (datetime.datetime | None | Unset): Filter runs created at or after this
            ISO timestamp (UTC)
        created_at_to (datetime.datetime | None | Unset): Filter runs created at or before this
            ISO timestamp (UTC)
        search (None | str | Unset): Search runs by input_values, output_data, error,
            session_alias (case-insensitive substring match)
        deep_search (bool | Unset): If true, also search run_message_history (slower but more
            comprehensive) Default: False.
        fields (list[RunField] | None | Unset): Optional list of fields to include per run. Always
            includes: id, workflow_id, machine_id, status, created_at. Provide multiple 'fields='
            params to include more.
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow, machine, machine.pools. Example: include=workflow,machine
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PaginatedResponseWithIncludesRunResponse
    """

    return sync_detailed(
        client=client,
        workflow_id=workflow_id,
        machine_id=machine_id,
        session_id=session_id,
        status=status,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        search=search,
        deep_search=deep_search,
        fields=fields,
        include=include,
        skip=skip,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    workflow_id: None | Unset | UUID = UNSET,
    machine_id: None | Unset | UUID = UNSET,
    session_id: None | Unset | UUID = UNSET,
    status: None | RunStatus | Unset = UNSET,
    created_at_from: datetime.datetime | None | Unset = UNSET,
    created_at_to: datetime.datetime | None | Unset = UNSET,
    search: None | str | Unset = UNSET,
    deep_search: bool | Unset = False,
    fields: list[RunField] | None | Unset = UNSET,
    include: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> Response[HTTPValidationError | PaginatedResponseWithIncludesRunResponse]:
    """List Runs

     List all runs for the authenticated organization.

    Supports pagination and filtering by workflow, machine, and status.
    Returns runs with their associated workflow and machine data.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.
    Resources are deduplicated across all items in the list.

    Args:
        workflow_id (None | Unset | UUID): Filter by workflow ID
        machine_id (None | Unset | UUID): Filter by machine ID
        session_id (None | Unset | UUID): Filter by session ID
        status (None | RunStatus | Unset): Filter by run status
        created_at_from (datetime.datetime | None | Unset): Filter runs created at or after this
            ISO timestamp (UTC)
        created_at_to (datetime.datetime | None | Unset): Filter runs created at or before this
            ISO timestamp (UTC)
        search (None | str | Unset): Search runs by input_values, output_data, error,
            session_alias (case-insensitive substring match)
        deep_search (bool | Unset): If true, also search run_message_history (slower but more
            comprehensive) Default: False.
        fields (list[RunField] | None | Unset): Optional list of fields to include per run. Always
            includes: id, workflow_id, machine_id, status, created_at. Provide multiple 'fields='
            params to include more.
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow, machine, machine.pools. Example: include=workflow,machine
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PaginatedResponseWithIncludesRunResponse]
    """

    kwargs = _get_kwargs(
        workflow_id=workflow_id,
        machine_id=machine_id,
        session_id=session_id,
        status=status,
        created_at_from=created_at_from,
        created_at_to=created_at_to,
        search=search,
        deep_search=deep_search,
        fields=fields,
        include=include,
        skip=skip,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    workflow_id: None | Unset | UUID = UNSET,
    machine_id: None | Unset | UUID = UNSET,
    session_id: None | Unset | UUID = UNSET,
    status: None | RunStatus | Unset = UNSET,
    created_at_from: datetime.datetime | None | Unset = UNSET,
    created_at_to: datetime.datetime | None | Unset = UNSET,
    search: None | str | Unset = UNSET,
    deep_search: bool | Unset = False,
    fields: list[RunField] | None | Unset = UNSET,
    include: None | str | Unset = UNSET,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
) -> HTTPValidationError | PaginatedResponseWithIncludesRunResponse | None:
    """List Runs

     List all runs for the authenticated organization.

    Supports pagination and filtering by workflow, machine, and status.
    Returns runs with their associated workflow and machine data.

    Use the `include` parameter to fetch related resources in the response.
    Related resources are returned in the `included` array following the JSON:API pattern.
    Resources are deduplicated across all items in the list.

    Args:
        workflow_id (None | Unset | UUID): Filter by workflow ID
        machine_id (None | Unset | UUID): Filter by machine ID
        session_id (None | Unset | UUID): Filter by session ID
        status (None | RunStatus | Unset): Filter by run status
        created_at_from (datetime.datetime | None | Unset): Filter runs created at or after this
            ISO timestamp (UTC)
        created_at_to (datetime.datetime | None | Unset): Filter runs created at or before this
            ISO timestamp (UTC)
        search (None | str | Unset): Search runs by input_values, output_data, error,
            session_alias (case-insensitive substring match)
        deep_search (bool | Unset): If true, also search run_message_history (slower but more
            comprehensive) Default: False.
        fields (list[RunField] | None | Unset): Optional list of fields to include per run. Always
            includes: id, workflow_id, machine_id, status, created_at. Provide multiple 'fields='
            params to include more.
        include (None | str | Unset): Comma-separated list of related resources to include.
            Allowed values: workflow, machine, machine.pools. Example: include=workflow,machine
        skip (int | Unset):  Default: 0.
        limit (int | Unset):  Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PaginatedResponseWithIncludesRunResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            workflow_id=workflow_id,
            machine_id=machine_id,
            session_id=session_id,
            status=status,
            created_at_from=created_at_from,
            created_at_to=created_at_to,
            search=search,
            deep_search=deep_search,
            fields=fields,
            include=include,
            skip=skip,
            limit=limit,
        )
    ).parsed

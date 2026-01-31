from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.workflow_tag_response import WorkflowTagResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    include_archived: bool | Unset = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["include_archived"] = include_archived

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/workflow-tags",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[WorkflowTagResponse] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = WorkflowTagResponse.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[HTTPValidationError | list[WorkflowTagResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    include_archived: bool | Unset = False,
) -> Response[HTTPValidationError | list[WorkflowTagResponse]]:
    """List Tags

     List all workflow tags for the organization.

    Tags are returned ordered by their group (ungrouped first), then by order within group.
    Each tag includes its workflow_count indicating how many workflows use it.

    Args:
        include_archived (bool | Unset): Include archived tags in the response Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[WorkflowTagResponse]]
    """

    kwargs = _get_kwargs(
        include_archived=include_archived,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    include_archived: bool | Unset = False,
) -> HTTPValidationError | list[WorkflowTagResponse] | None:
    """List Tags

     List all workflow tags for the organization.

    Tags are returned ordered by their group (ungrouped first), then by order within group.
    Each tag includes its workflow_count indicating how many workflows use it.

    Args:
        include_archived (bool | Unset): Include archived tags in the response Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[WorkflowTagResponse]
    """

    return sync_detailed(
        client=client,
        include_archived=include_archived,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    include_archived: bool | Unset = False,
) -> Response[HTTPValidationError | list[WorkflowTagResponse]]:
    """List Tags

     List all workflow tags for the organization.

    Tags are returned ordered by their group (ungrouped first), then by order within group.
    Each tag includes its workflow_count indicating how many workflows use it.

    Args:
        include_archived (bool | Unset): Include archived tags in the response Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[WorkflowTagResponse]]
    """

    kwargs = _get_kwargs(
        include_archived=include_archived,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    include_archived: bool | Unset = False,
) -> HTTPValidationError | list[WorkflowTagResponse] | None:
    """List Tags

     List all workflow tags for the organization.

    Tags are returned ordered by their group (ungrouped first), then by order within group.
    Each tag includes its workflow_count indicating how many workflows use it.

    Args:
        include_archived (bool | Unset): Include archived tags in the response Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[WorkflowTagResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            include_archived=include_archived,
        )
    ).parsed

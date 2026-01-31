from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.workflow_tag_response import WorkflowTagResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    tag_id: UUID,
    *,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/workflow-tags/{tag_id}/unarchive".format(
            tag_id=quote(str(tag_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | WorkflowTagResponse | None:
    if response.status_code == 200:
        response_200 = WorkflowTagResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | WorkflowTagResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    tag_id: UUID,
    *,
    client: AuthenticatedClient,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | WorkflowTagResponse]:
    """Unarchive Tag

     Unarchive a workflow tag.

    Restores an archived tag so it can be assigned to workflows again.

    Args:
        tag_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | WorkflowTagResponse]
    """

    kwargs = _get_kwargs(
        tag_id=tag_id,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    tag_id: UUID,
    *,
    client: AuthenticatedClient,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | WorkflowTagResponse | None:
    """Unarchive Tag

     Unarchive a workflow tag.

    Restores an archived tag so it can be assigned to workflows again.

    Args:
        tag_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | WorkflowTagResponse
    """

    return sync_detailed(
        tag_id=tag_id,
        client=client,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    tag_id: UUID,
    *,
    client: AuthenticatedClient,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | WorkflowTagResponse]:
    """Unarchive Tag

     Unarchive a workflow tag.

    Restores an archived tag so it can be assigned to workflows again.

    Args:
        tag_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | WorkflowTagResponse]
    """

    kwargs = _get_kwargs(
        tag_id=tag_id,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    tag_id: UUID,
    *,
    client: AuthenticatedClient,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | WorkflowTagResponse | None:
    """Unarchive Tag

     Unarchive a workflow tag.

    Restores an archived tag so it can be assigned to workflows again.

    Args:
        tag_id (UUID):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | WorkflowTagResponse
    """

    return (
        await asyncio_detailed(
            tag_id=tag_id,
            client=client,
            idempotency_key=idempotency_key,
        )
    ).parsed

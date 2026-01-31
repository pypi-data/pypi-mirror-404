from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.copy_to_clipboard_request import CopyToClipboardRequest
from ...models.copy_to_clipboard_v1_computer_machine_id_copy_to_clipboard_post_response_copy_to_clipboard_v1_computer_machine_id_copy_to_clipboard_post import (
    CopyToClipboardV1ComputerMachineIdCopyToClipboardPostResponseCopyToClipboardV1ComputerMachineIdCopyToClipboardPost,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    machine_id: str,
    *,
    body: CopyToClipboardRequest,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/computer/{machine_id}/copy_to_clipboard".format(
            machine_id=quote(str(machine_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CopyToClipboardV1ComputerMachineIdCopyToClipboardPostResponseCopyToClipboardV1ComputerMachineIdCopyToClipboardPost
    | HTTPValidationError
    | None
):
    if response.status_code == 200:
        response_200 = CopyToClipboardV1ComputerMachineIdCopyToClipboardPostResponseCopyToClipboardV1ComputerMachineIdCopyToClipboardPost.from_dict(
            response.json()
        )

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
) -> Response[
    CopyToClipboardV1ComputerMachineIdCopyToClipboardPostResponseCopyToClipboardV1ComputerMachineIdCopyToClipboardPost
    | HTTPValidationError
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    machine_id: str,
    *,
    client: AuthenticatedClient,
    body: CopyToClipboardRequest,
    idempotency_key: str | Unset = UNSET,
) -> Response[
    CopyToClipboardV1ComputerMachineIdCopyToClipboardPostResponseCopyToClipboardV1ComputerMachineIdCopyToClipboardPost
    | HTTPValidationError
]:
    """Copy to clipboard via Ctrl+C

     Execute Ctrl+C and return clipboard contents with the specified key name.

    Args:
        machine_id (str):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (CopyToClipboardRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CopyToClipboardV1ComputerMachineIdCopyToClipboardPostResponseCopyToClipboardV1ComputerMachineIdCopyToClipboardPost | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        machine_id=machine_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    machine_id: str,
    *,
    client: AuthenticatedClient,
    body: CopyToClipboardRequest,
    idempotency_key: str | Unset = UNSET,
) -> (
    CopyToClipboardV1ComputerMachineIdCopyToClipboardPostResponseCopyToClipboardV1ComputerMachineIdCopyToClipboardPost
    | HTTPValidationError
    | None
):
    """Copy to clipboard via Ctrl+C

     Execute Ctrl+C and return clipboard contents with the specified key name.

    Args:
        machine_id (str):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (CopyToClipboardRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CopyToClipboardV1ComputerMachineIdCopyToClipboardPostResponseCopyToClipboardV1ComputerMachineIdCopyToClipboardPost | HTTPValidationError
    """

    return sync_detailed(
        machine_id=machine_id,
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    machine_id: str,
    *,
    client: AuthenticatedClient,
    body: CopyToClipboardRequest,
    idempotency_key: str | Unset = UNSET,
) -> Response[
    CopyToClipboardV1ComputerMachineIdCopyToClipboardPostResponseCopyToClipboardV1ComputerMachineIdCopyToClipboardPost
    | HTTPValidationError
]:
    """Copy to clipboard via Ctrl+C

     Execute Ctrl+C and return clipboard contents with the specified key name.

    Args:
        machine_id (str):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (CopyToClipboardRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CopyToClipboardV1ComputerMachineIdCopyToClipboardPostResponseCopyToClipboardV1ComputerMachineIdCopyToClipboardPost | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        machine_id=machine_id,
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    machine_id: str,
    *,
    client: AuthenticatedClient,
    body: CopyToClipboardRequest,
    idempotency_key: str | Unset = UNSET,
) -> (
    CopyToClipboardV1ComputerMachineIdCopyToClipboardPostResponseCopyToClipboardV1ComputerMachineIdCopyToClipboardPost
    | HTTPValidationError
    | None
):
    """Copy to clipboard via Ctrl+C

     Execute Ctrl+C and return clipboard contents with the specified key name.

    Args:
        machine_id (str):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (CopyToClipboardRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CopyToClipboardV1ComputerMachineIdCopyToClipboardPostResponseCopyToClipboardV1ComputerMachineIdCopyToClipboardPost | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            machine_id=machine_id,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed

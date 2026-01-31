from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.power_shell_exec_request import PowerShellExecRequest
from ...models.powershell_exec_v1_computer_machine_id_shell_powershell_exec_post_response_powershell_exec_v1_computer_machine_id_shell_powershell_exec_post import (
    PowershellExecV1ComputerMachineIdShellPowershellExecPostResponsePowershellExecV1ComputerMachineIdShellPowershellExecPost,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    machine_id: str,
    *,
    body: PowerShellExecRequest,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/computer/{machine_id}/shell/powershell/exec".format(
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
    HTTPValidationError
    | PowershellExecV1ComputerMachineIdShellPowershellExecPostResponsePowershellExecV1ComputerMachineIdShellPowershellExecPost
    | None
):
    if response.status_code == 200:
        response_200 = PowershellExecV1ComputerMachineIdShellPowershellExecPostResponsePowershellExecV1ComputerMachineIdShellPowershellExecPost.from_dict(
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
    HTTPValidationError
    | PowershellExecV1ComputerMachineIdShellPowershellExecPostResponsePowershellExecV1ComputerMachineIdShellPowershellExecPost
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
    body: PowerShellExecRequest,
    idempotency_key: str | Unset = UNSET,
) -> Response[
    HTTPValidationError
    | PowershellExecV1ComputerMachineIdShellPowershellExecPostResponsePowershellExecV1ComputerMachineIdShellPowershellExecPost
]:
    """Execute PowerShell command

     Execute PowerShell command on the machine.

    Args:
        machine_id (str):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (PowerShellExecRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PowershellExecV1ComputerMachineIdShellPowershellExecPostResponsePowershellExecV1ComputerMachineIdShellPowershellExecPost]
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
    body: PowerShellExecRequest,
    idempotency_key: str | Unset = UNSET,
) -> (
    HTTPValidationError
    | PowershellExecV1ComputerMachineIdShellPowershellExecPostResponsePowershellExecV1ComputerMachineIdShellPowershellExecPost
    | None
):
    """Execute PowerShell command

     Execute PowerShell command on the machine.

    Args:
        machine_id (str):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (PowerShellExecRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PowershellExecV1ComputerMachineIdShellPowershellExecPostResponsePowershellExecV1ComputerMachineIdShellPowershellExecPost
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
    body: PowerShellExecRequest,
    idempotency_key: str | Unset = UNSET,
) -> Response[
    HTTPValidationError
    | PowershellExecV1ComputerMachineIdShellPowershellExecPostResponsePowershellExecV1ComputerMachineIdShellPowershellExecPost
]:
    """Execute PowerShell command

     Execute PowerShell command on the machine.

    Args:
        machine_id (str):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (PowerShellExecRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PowershellExecV1ComputerMachineIdShellPowershellExecPostResponsePowershellExecV1ComputerMachineIdShellPowershellExecPost]
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
    body: PowerShellExecRequest,
    idempotency_key: str | Unset = UNSET,
) -> (
    HTTPValidationError
    | PowershellExecV1ComputerMachineIdShellPowershellExecPostResponsePowershellExecV1ComputerMachineIdShellPowershellExecPost
    | None
):
    """Execute PowerShell command

     Execute PowerShell command on the machine.

    Args:
        machine_id (str):
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (PowerShellExecRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PowershellExecV1ComputerMachineIdShellPowershellExecPostResponsePowershellExecV1ComputerMachineIdShellPowershellExecPost
    """

    return (
        await asyncio_detailed(
            machine_id=machine_id,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed

from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.workflow_prompt_image_signed_url_response import WorkflowPromptImageSignedUrlResponse
from ...types import UNSET, Response


def _get_kwargs(
    *,
    path: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["path"] = path

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/workflows/prompt-image/signed-url",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | WorkflowPromptImageSignedUrlResponse | None:
    if response.status_code == 200:
        response_200 = WorkflowPromptImageSignedUrlResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | WorkflowPromptImageSignedUrlResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    path: str,
) -> Response[HTTPValidationError | WorkflowPromptImageSignedUrlResponse]:
    """Get signed URL for a prompt image

     Get a fresh signed URL for an existing workflow prompt image.

    Args:
        path (str): The storage path of the image (e.g., org_xxx/prompt-assets/image.png)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | WorkflowPromptImageSignedUrlResponse]
    """

    kwargs = _get_kwargs(
        path=path,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    path: str,
) -> HTTPValidationError | WorkflowPromptImageSignedUrlResponse | None:
    """Get signed URL for a prompt image

     Get a fresh signed URL for an existing workflow prompt image.

    Args:
        path (str): The storage path of the image (e.g., org_xxx/prompt-assets/image.png)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | WorkflowPromptImageSignedUrlResponse
    """

    return sync_detailed(
        client=client,
        path=path,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    path: str,
) -> Response[HTTPValidationError | WorkflowPromptImageSignedUrlResponse]:
    """Get signed URL for a prompt image

     Get a fresh signed URL for an existing workflow prompt image.

    Args:
        path (str): The storage path of the image (e.g., org_xxx/prompt-assets/image.png)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | WorkflowPromptImageSignedUrlResponse]
    """

    kwargs = _get_kwargs(
        path=path,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    path: str,
) -> HTTPValidationError | WorkflowPromptImageSignedUrlResponse | None:
    """Get signed URL for a prompt image

     Get a fresh signed URL for an existing workflow prompt image.

    Args:
        path (str): The storage path of the image (e.g., org_xxx/prompt-assets/image.png)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | WorkflowPromptImageSignedUrlResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            path=path,
        )
    ).parsed

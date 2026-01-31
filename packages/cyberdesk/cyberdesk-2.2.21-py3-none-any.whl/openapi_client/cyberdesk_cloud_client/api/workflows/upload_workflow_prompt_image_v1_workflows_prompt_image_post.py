from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.body_upload_workflow_prompt_image_v1_workflows_prompt_image_post import (
    BodyUploadWorkflowPromptImageV1WorkflowsPromptImagePost,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.workflow_prompt_image_response import WorkflowPromptImageResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: BodyUploadWorkflowPromptImageV1WorkflowsPromptImagePost,
    idempotency_key: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/workflows/prompt-image",
    }

    _kwargs["files"] = body.to_multipart()

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | WorkflowPromptImageResponse | None:
    if response.status_code == 201:
        response_201 = WorkflowPromptImageResponse.from_dict(response.json())

        return response_201

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | WorkflowPromptImageResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: BodyUploadWorkflowPromptImageV1WorkflowsPromptImagePost,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | WorkflowPromptImageResponse]:
    r"""Upload a workflow prompt image

     Upload an image to use in workflow prompts.

    The returned `supabase_url` can be embedded directly in workflow prompt HTML:

    ```html
    <img src=\"supabase://workflow-prompt-images/org_xxx/prompt-assets/my-image.png\"
    alt=\"Description\">
    ```

    When the workflow runs, Cyberdesk automatically resolves these URLs to display the image
    to the AI agent.

    Supported formats: PNG, JPEG, GIF, WebP. Maximum size: 10MB.

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (BodyUploadWorkflowPromptImageV1WorkflowsPromptImagePost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | WorkflowPromptImageResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: BodyUploadWorkflowPromptImageV1WorkflowsPromptImagePost,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | WorkflowPromptImageResponse | None:
    r"""Upload a workflow prompt image

     Upload an image to use in workflow prompts.

    The returned `supabase_url` can be embedded directly in workflow prompt HTML:

    ```html
    <img src=\"supabase://workflow-prompt-images/org_xxx/prompt-assets/my-image.png\"
    alt=\"Description\">
    ```

    When the workflow runs, Cyberdesk automatically resolves these URLs to display the image
    to the AI agent.

    Supported formats: PNG, JPEG, GIF, WebP. Maximum size: 10MB.

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (BodyUploadWorkflowPromptImageV1WorkflowsPromptImagePost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | WorkflowPromptImageResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        idempotency_key=idempotency_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: BodyUploadWorkflowPromptImageV1WorkflowsPromptImagePost,
    idempotency_key: str | Unset = UNSET,
) -> Response[HTTPValidationError | WorkflowPromptImageResponse]:
    r"""Upload a workflow prompt image

     Upload an image to use in workflow prompts.

    The returned `supabase_url` can be embedded directly in workflow prompt HTML:

    ```html
    <img src=\"supabase://workflow-prompt-images/org_xxx/prompt-assets/my-image.png\"
    alt=\"Description\">
    ```

    When the workflow runs, Cyberdesk automatically resolves these URLs to display the image
    to the AI agent.

    Supported formats: PNG, JPEG, GIF, WebP. Maximum size: 10MB.

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (BodyUploadWorkflowPromptImageV1WorkflowsPromptImagePost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | WorkflowPromptImageResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: BodyUploadWorkflowPromptImageV1WorkflowsPromptImagePost,
    idempotency_key: str | Unset = UNSET,
) -> HTTPValidationError | WorkflowPromptImageResponse | None:
    r"""Upload a workflow prompt image

     Upload an image to use in workflow prompts.

    The returned `supabase_url` can be embedded directly in workflow prompt HTML:

    ```html
    <img src=\"supabase://workflow-prompt-images/org_xxx/prompt-assets/my-image.png\"
    alt=\"Description\">
    ```

    When the workflow runs, Cyberdesk automatically resolves these URLs to display the image
    to the AI agent.

    Supported formats: PNG, JPEG, GIF, WebP. Maximum size: 10MB.

    Args:
        idempotency_key (str | Unset):  Example: 550e8400-e29b-41d4-a716-446655440000.
        body (BodyUploadWorkflowPromptImageV1WorkflowsPromptImagePost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | WorkflowPromptImageResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            idempotency_key=idempotency_key,
        )
    ).parsed

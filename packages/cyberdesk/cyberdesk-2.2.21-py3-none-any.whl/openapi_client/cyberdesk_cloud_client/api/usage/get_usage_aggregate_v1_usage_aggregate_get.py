import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.usage_aggregate_response import UsageAggregateResponse
from ...models.usage_mode import UsageMode
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    from_date: datetime.datetime,
    to_date: datetime.datetime,
    mode: UsageMode | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_from_date = from_date.isoformat()
    params["from_date"] = json_from_date

    json_to_date = to_date.isoformat()
    params["to_date"] = json_to_date

    json_mode: str | Unset = UNSET
    if not isinstance(mode, Unset):
        json_mode = mode.value

    params["mode"] = json_mode

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/usage/aggregate",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | UsageAggregateResponse | None:
    if response.status_code == 200:
        response_200 = UsageAggregateResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | UsageAggregateResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    from_date: datetime.datetime,
    to_date: datetime.datetime,
    mode: UsageMode | Unset = UNSET,
) -> Response[HTTPValidationError | UsageAggregateResponse]:
    """Get Usage Aggregate

     Aggregate usage (agentic and cached steps) for a given date range.

    Two modes are supported:
    - **simulated** (default): Uses total_agentic_steps and total_cached_steps from usage_metadata,
      but excludes runs where billing_outcome is 'infra_failure' (these would have been free).
      Use this for customers not yet on Stripe billing.
    - **billed**: Uses total_agentic_steps_billed and total_cached_steps_billed.
      Use this for customers on active Stripe billing.

    Args:
        from_date (datetime.datetime): Start of period (inclusive, ISO format)
        to_date (datetime.datetime): End of period (exclusive, ISO format)
        mode (UsageMode | Unset): Mode for counting usage steps.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | UsageAggregateResponse]
    """

    kwargs = _get_kwargs(
        from_date=from_date,
        to_date=to_date,
        mode=mode,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    from_date: datetime.datetime,
    to_date: datetime.datetime,
    mode: UsageMode | Unset = UNSET,
) -> HTTPValidationError | UsageAggregateResponse | None:
    """Get Usage Aggregate

     Aggregate usage (agentic and cached steps) for a given date range.

    Two modes are supported:
    - **simulated** (default): Uses total_agentic_steps and total_cached_steps from usage_metadata,
      but excludes runs where billing_outcome is 'infra_failure' (these would have been free).
      Use this for customers not yet on Stripe billing.
    - **billed**: Uses total_agentic_steps_billed and total_cached_steps_billed.
      Use this for customers on active Stripe billing.

    Args:
        from_date (datetime.datetime): Start of period (inclusive, ISO format)
        to_date (datetime.datetime): End of period (exclusive, ISO format)
        mode (UsageMode | Unset): Mode for counting usage steps.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | UsageAggregateResponse
    """

    return sync_detailed(
        client=client,
        from_date=from_date,
        to_date=to_date,
        mode=mode,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    from_date: datetime.datetime,
    to_date: datetime.datetime,
    mode: UsageMode | Unset = UNSET,
) -> Response[HTTPValidationError | UsageAggregateResponse]:
    """Get Usage Aggregate

     Aggregate usage (agentic and cached steps) for a given date range.

    Two modes are supported:
    - **simulated** (default): Uses total_agentic_steps and total_cached_steps from usage_metadata,
      but excludes runs where billing_outcome is 'infra_failure' (these would have been free).
      Use this for customers not yet on Stripe billing.
    - **billed**: Uses total_agentic_steps_billed and total_cached_steps_billed.
      Use this for customers on active Stripe billing.

    Args:
        from_date (datetime.datetime): Start of period (inclusive, ISO format)
        to_date (datetime.datetime): End of period (exclusive, ISO format)
        mode (UsageMode | Unset): Mode for counting usage steps.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | UsageAggregateResponse]
    """

    kwargs = _get_kwargs(
        from_date=from_date,
        to_date=to_date,
        mode=mode,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    from_date: datetime.datetime,
    to_date: datetime.datetime,
    mode: UsageMode | Unset = UNSET,
) -> HTTPValidationError | UsageAggregateResponse | None:
    """Get Usage Aggregate

     Aggregate usage (agentic and cached steps) for a given date range.

    Two modes are supported:
    - **simulated** (default): Uses total_agentic_steps and total_cached_steps from usage_metadata,
      but excludes runs where billing_outcome is 'infra_failure' (these would have been free).
      Use this for customers not yet on Stripe billing.
    - **billed**: Uses total_agentic_steps_billed and total_cached_steps_billed.
      Use this for customers on active Stripe billing.

    Args:
        from_date (datetime.datetime): Start of period (inclusive, ISO format)
        to_date (datetime.datetime): End of period (exclusive, ISO format)
        mode (UsageMode | Unset): Mode for counting usage steps.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | UsageAggregateResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            from_date=from_date,
            to_date=to_date,
            mode=mode,
        )
    ).parsed

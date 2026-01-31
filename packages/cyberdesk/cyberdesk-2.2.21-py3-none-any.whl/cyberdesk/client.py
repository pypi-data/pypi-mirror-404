"""Cyberdesk Python SDK Client."""
from typing import Optional, Dict, Any, Union, List, TypeVar, Generic, Callable
from uuid import UUID, uuid4
from pathlib import Path
import asyncio
import random
import time
import httpx
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# Import the generated client
from openapi_client.cyberdesk_cloud_client import AuthenticatedClient
from openapi_client.cyberdesk_cloud_client.types import UNSET, Unset
from openapi_client.cyberdesk_cloud_client.api.machines import (
    list_machines_v1_machines_get,
    create_machine_v1_machines_post,
    get_machine_v1_machines_machine_id_get,
    update_machine_v1_machines_machine_id_patch,
    delete_machine_v1_machines_machine_id_delete,
    get_machine_pools_v1_machines_machine_id_pools_get,
    update_machine_pools_v1_machines_machine_id_pools_put,
)
from openapi_client.cyberdesk_cloud_client.api.pools import (
    list_pools_v1_pools_get,
    create_pool_v1_pools_post,
    get_pool_v1_pools_pool_id_get,
    update_pool_v1_pools_pool_id_patch,
    delete_pool_v1_pools_pool_id_delete,
    add_machines_to_pool_v1_pools_pool_id_machines_post,
    remove_machines_from_pool_v1_pools_pool_id_machines_delete,
)
from openapi_client.cyberdesk_cloud_client.api.workflows import (
    list_workflows_v1_workflows_get,
    create_workflow_v1_workflows_post,
    get_workflow_v1_workflows_workflow_id_get,
    update_workflow_v1_workflows_workflow_id_patch,
    delete_workflow_v1_workflows_workflow_id_delete,
    upload_workflow_prompt_image_v1_workflows_prompt_image_post,
    list_workflow_prompt_images_v1_workflows_prompt_images_get,
    get_workflow_prompt_image_signed_url_v1_workflows_prompt_image_signed_url_get,
    delete_workflow_prompt_image_v1_workflows_prompt_image_delete,
)
from openapi_client.cyberdesk_cloud_client.api.runs import (
    list_runs_v1_runs_get,
    create_run_v1_runs_post,
    get_run_v1_runs_run_id_get,
    update_run_v1_runs_run_id_patch,
    delete_run_v1_runs_run_id_delete,
    bulk_create_runs_v1_runs_bulk_post,
    create_run_chain_v1_runs_chain_post,
    retry_run_v1_runs_run_id_retry_post,
)
from openapi_client.cyberdesk_cloud_client.api.connections import (
    list_connections_v1_connections_get,
    create_connection_v1_connections_post,
)
from openapi_client.cyberdesk_cloud_client.api.trajectories import (
    list_trajectories_v1_trajectories_get,
    create_trajectory_v1_trajectories_post,
    get_trajectory_v1_trajectories_trajectory_id_get,
    update_trajectory_v1_trajectories_trajectory_id_patch,
    delete_trajectory_v1_trajectories_trajectory_id_delete,
    get_latest_trajectory_for_workflow_v1_workflows_workflow_id_latest_trajectory_get,
    duplicate_trajectory_v1_trajectories_trajectory_id_duplicate_post,
)
from openapi_client.cyberdesk_cloud_client.api.run_attachments import (
    list_run_attachments_v1_run_attachments_get,
    create_run_attachment_v1_run_attachments_post,
    get_run_attachment_v1_run_attachments_attachment_id_get,
    download_run_attachment_v1_run_attachments_attachment_id_download_get,
    get_run_attachment_download_url_v1_run_attachments_attachment_id_download_url_get,
    update_run_attachment_v1_run_attachments_attachment_id_put,
    delete_run_attachment_v1_run_attachments_attachment_id_delete,
)
from openapi_client.cyberdesk_cloud_client.api.model_configurations import (
    list_model_configurations_v1_model_configurations_get,
    create_model_configuration_v1_model_configurations_post,
    get_model_configuration_v1_model_configurations_model_configuration_id_get,
    update_model_configuration_v1_model_configurations_model_configuration_id_patch,
    delete_model_configuration_v1_model_configurations_model_configuration_id_delete,
)
from openapi_client.cyberdesk_cloud_client.api.usage import (
    get_usage_aggregate_v1_usage_aggregate_get,
)
from openapi_client.cyberdesk_cloud_client.api.workflow_tags import (
    list_tags_v1_workflow_tags_get,
    create_tag_v1_workflow_tags_post,
    get_tag_v1_workflow_tags_tag_id_get,
    update_tag_v1_workflow_tags_tag_id_patch,
    delete_tag_v1_workflow_tags_tag_id_delete,
    archive_tag_v1_workflow_tags_tag_id_archive_post,
    unarchive_tag_v1_workflow_tags_tag_id_unarchive_post,
    reorder_tags_v1_workflow_tags_reorder_put,
)
from openapi_client.cyberdesk_cloud_client.api.workflow_tag_groups import (
    list_tag_groups_v1_workflow_tag_groups_get,
    create_tag_group_v1_workflow_tag_groups_post,
    get_tag_group_v1_workflow_tag_groups_group_id_get,
    update_tag_group_v1_workflow_tag_groups_group_id_patch,
    delete_tag_group_v1_workflow_tag_groups_group_id_delete,
    reorder_tag_groups_v1_workflow_tag_groups_reorder_put,
)
from openapi_client.cyberdesk_cloud_client.api.workflows import (
    add_tags_to_workflow_v1_workflows_workflow_id_tags_post,
    remove_tag_from_workflow_v1_workflows_workflow_id_tags_tag_id_delete,
    get_workflow_tags_v1_workflows_workflow_id_tags_get,
    bulk_add_tags_to_workflows_v1_workflows_bulk_tags_post,
)

# Import models
from openapi_client.cyberdesk_cloud_client.models import (
    MachineCreate,
    MachineUpdate,
    MachineResponse,
    MachineStatus,
    MachinePoolUpdate,
    PoolCreate,
    PoolUpdate,
    PoolResponse,
    PoolWithMachines,
    MachinePoolAssignment,
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    RunCreate,
    RunUpdate,
    RunResponse,
    RunStatus,
    RunBulkCreate,
    RunBulkCreateResponse,
    WorkflowChainCreate,
    WorkflowChainResponse,
    FileInput,
    ConnectionCreate,
    ConnectionResponse,
    ConnectionStatus,
    TrajectoryCreate,
    TrajectoryUpdate,
    TrajectoryResponse,
    RunAttachmentCreate,
    RunAttachmentUpdate,
    RunAttachmentResponse,
    RunAttachmentDownloadUrlResponse,
    AttachmentType,
    IncludedResource,
    PaginatedResponseWithIncludesMachineResponse,
    PaginatedResponseWithIncludesPoolResponse,
    PaginatedResponseWorkflowResponse,
    PaginatedResponseWithIncludesRunResponse,
    PaginatedResponseConnectionResponse,
    PaginatedResponseWithIncludesTrajectoryResponse,
    PaginatedResponseRunAttachmentResponse,
    RunRetry,
    RunField,
    ModelConfigurationCreate,
    ModelConfigurationUpdate,
    ModelConfigurationResponse,
    UsageAggregateResponse,
    UsageMode,
    WorkflowPromptImageResponse,
    WorkflowPromptImageListItem,
    WorkflowPromptImageSignedUrlResponse,
    BodyUploadWorkflowPromptImageV1WorkflowsPromptImagePost,
    WorkflowTagCreate,
    WorkflowTagUpdate,
    WorkflowTagResponse,
    WorkflowTagGroupCreate,
    WorkflowTagGroupUpdate,
    WorkflowTagGroupResponse,
    ReorderRequest,
    AddTagsRequest,
    BulkAddTagsRequest,
)
from openapi_client.cyberdesk_cloud_client.types import File as OpenAPIFile

# Re-export common types
__all__ = [
    # Client
    "CyberdeskClient",
    # Machine types
    "MachineCreate",
    "MachineUpdate",
    "MachineResponse",
    "MachineStatus",
    "MachinePoolUpdate",
    # Pool types
    "PoolCreate",
    "PoolUpdate",
    "PoolResponse",
    "PoolWithMachines",
    "MachinePoolAssignment",
    # Workflow types
    "WorkflowCreate",
    "WorkflowUpdate",
    "WorkflowResponse",
    "WorkflowPromptImageResponse",
    "WorkflowPromptImageListItem",
    "WorkflowPromptImageSignedUrlResponse",
    # Run types
    "RunCreate",
    "RunUpdate",
    "RunResponse",
    "RunStatus",
    "RunBulkCreate",
    "RunBulkCreateResponse",
    "WorkflowChainCreate",
    "WorkflowChainResponse",
    "FileInput",
    "RunRetry",
    "RunField",
    # Connection types
    "ConnectionCreate",
    "ConnectionResponse",
    "ConnectionStatus",
    # Trajectory types
    "TrajectoryCreate",
    "TrajectoryUpdate",
    "TrajectoryResponse",
    # Attachment types
    "RunAttachmentCreate",
    "RunAttachmentUpdate",
    "RunAttachmentResponse",
    "RunAttachmentDownloadUrlResponse",
    "AttachmentType",
    # Include types
    "IncludedResource",
    # Model configuration types
    "ModelConfigurationCreate",
    "ModelConfigurationUpdate",
    "ModelConfigurationResponse",
    # Usage types
    "UsageAggregateResponse",
    "UsageMode",
    # Workflow Tag types
    "WorkflowTagCreate",
    "WorkflowTagUpdate",
    "WorkflowTagResponse",
    "WorkflowTagGroupCreate",
    "WorkflowTagGroupUpdate",
    "WorkflowTagGroupResponse",
    "ReorderRequest",
    "AddTagsRequest",
    "BulkAddTagsRequest",
]

DEFAULT_API_BASE_URL = "https://api.cyberdesk.io"


T = TypeVar('T')

@dataclass
class ApiResponse(Generic[T]):
    """Wrapper for API responses."""
    data: Optional[T] = None
    error: Optional[Any] = None


@dataclass
class RetryConfig:
    """Retry configuration for transient failures."""

    max_retries: int = 3
    min_delay_seconds: float = 0.25
    max_delay_seconds: float = 8.0
    on_retry: Optional[
        Callable[[Dict[str, Any]], None]
    ] = None  # called with {attempt, max_retries, delay_seconds, reason, status_code?}


def _is_write_method(method: str) -> bool:
    m = method.upper()
    return m in ("POST", "PUT", "PATCH", "DELETE")


def _parse_retry_after_seconds(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    v = value.strip()
    if not v:
        return None

    # Seconds
    if v.isdigit():
        try:
            seconds = int(v)
        except Exception:
            return None
        return max(0.0, float(seconds))

    # HTTP date
    try:
        dt = parsedate_to_datetime(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return max(0.0, (dt - now).total_seconds())
    except Exception:
        return None


def _compute_backoff_seconds(attempt: int, min_delay: float, max_delay: float) -> float:
    # Full jitter: random(0, min(max_delay, min_delay * 2^attempt))
    exp = min(max_delay, min_delay * (2 ** attempt))
    return random.random() * exp


def _should_retry_response(response: httpx.Response) -> bool:
    if response.status_code in (408, 429, 500, 502, 503, 504):
        return True
    if response.status_code == 409:
        idem_status = response.headers.get("Idempotency-Status", "").lower()
        if idem_status == "in_progress":
            return True
    return False


def _ensure_idempotency_header(
    headers: Optional[Dict[str, str]],
    *,
    enabled: bool,
    header_name: str,
    key_generator: Callable[[], str],
    method: str,
) -> tuple[Optional[Dict[str, str]], Optional[str]]:
    """
    Ensure an Idempotency-Key header exists for write requests.

    Returns:
        (headers_dict, idempotency_key_used)
    """
    if not enabled or not _is_write_method(method):
        return headers, None

    header_name_l = header_name.lower()
    existing = None
    if headers:
        for k in headers.keys():
            if k.lower() == header_name_l:
                existing = headers[k]
                break
    if existing:
        return headers, existing

    key = key_generator()
    out = dict(headers or {})
    out[header_name] = key
    return out, key


def _has_header_case_insensitive(headers: Optional[Dict[str, str]], header_name: str) -> bool:
    if not headers:
        return False
    target = header_name.lower()
    return any(k.lower() == target for k in headers.keys())


class RetryingClient(httpx.Client):
    def __init__(
        self,
        *args: Any,
        retry: RetryConfig,
        idempotency_enabled: bool,
        idempotency_header_name: str,
        idempotency_key_generator: Callable[[], str],
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._retry = retry
        self._idempotency_enabled = idempotency_enabled
        self._idempotency_header_name = idempotency_header_name
        self._idempotency_key_generator = idempotency_key_generator

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:  # type: ignore[override]
        headers, _idem = _ensure_idempotency_header(
            kwargs.get("headers"),
            enabled=self._idempotency_enabled,
            header_name=self._idempotency_header_name,
            key_generator=self._idempotency_key_generator,
            method=method,
        )
        kwargs["headers"] = headers

        # Safety: never retry write requests unless an Idempotency-Key is present.
        safe_to_retry = (not _is_write_method(method)) or _has_header_case_insensitive(headers, self._idempotency_header_name)
        if not safe_to_retry:
            return super().request(method, url, **kwargs)

        max_retries = max(0, int(self._retry.max_retries))
        for attempt in range(0, max_retries + 1):
            try:
                response = super().request(method, url, **kwargs)
            except httpx.TimeoutException as e:
                if attempt >= max_retries:
                    raise
                delay = _compute_backoff_seconds(attempt, self._retry.min_delay_seconds, self._retry.max_delay_seconds)
                self._retry.on_retry and self._retry.on_retry(
                    {
                        "attempt": attempt,
                        "max_retries": max_retries,
                        "delay_seconds": delay,
                        "reason": "timeout",
                    }
                )
                time.sleep(delay)
                continue
            except httpx.RequestError as e:
                if attempt >= max_retries:
                    raise
                delay = _compute_backoff_seconds(attempt, self._retry.min_delay_seconds, self._retry.max_delay_seconds)
                self._retry.on_retry and self._retry.on_retry(
                    {
                        "attempt": attempt,
                        "max_retries": max_retries,
                        "delay_seconds": delay,
                        "reason": "network_error",
                    }
                )
                time.sleep(delay)
                continue

            if not _should_retry_response(response) or attempt >= max_retries:
                return response

            retry_after = _parse_retry_after_seconds(response.headers.get("Retry-After"))
            delay = retry_after if retry_after is not None else _compute_backoff_seconds(attempt, self._retry.min_delay_seconds, self._retry.max_delay_seconds)
            delay = min(self._retry.max_delay_seconds, max(0.0, delay))

            self._retry.on_retry and self._retry.on_retry(
                {
                    "attempt": attempt,
                    "max_retries": max_retries,
                    "delay_seconds": delay,
                    "reason": "http_status",
                    "status_code": response.status_code,
                }
            )

            response.close()
            time.sleep(delay)

        # Defensive: should never reach
        return super().request(method, url, **kwargs)


class RetryingAsyncClient(httpx.AsyncClient):
    def __init__(
        self,
        *args: Any,
        retry: RetryConfig,
        idempotency_enabled: bool,
        idempotency_header_name: str,
        idempotency_key_generator: Callable[[], str],
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._retry = retry
        self._idempotency_enabled = idempotency_enabled
        self._idempotency_header_name = idempotency_header_name
        self._idempotency_key_generator = idempotency_key_generator

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:  # type: ignore[override]
        headers, _idem = _ensure_idempotency_header(
            kwargs.get("headers"),
            enabled=self._idempotency_enabled,
            header_name=self._idempotency_header_name,
            key_generator=self._idempotency_key_generator,
            method=method,
        )
        kwargs["headers"] = headers

        # Safety: never retry write requests unless an Idempotency-Key is present.
        safe_to_retry = (not _is_write_method(method)) or _has_header_case_insensitive(headers, self._idempotency_header_name)
        if not safe_to_retry:
            return await super().request(method, url, **kwargs)

        max_retries = max(0, int(self._retry.max_retries))
        for attempt in range(0, max_retries + 1):
            try:
                response = await super().request(method, url, **kwargs)
            except httpx.TimeoutException:
                if attempt >= max_retries:
                    raise
                delay = _compute_backoff_seconds(attempt, self._retry.min_delay_seconds, self._retry.max_delay_seconds)
                self._retry.on_retry and self._retry.on_retry(
                    {
                        "attempt": attempt,
                        "max_retries": max_retries,
                        "delay_seconds": delay,
                        "reason": "timeout",
                    }
                )
                await asyncio.sleep(delay)
                continue
            except httpx.RequestError:
                if attempt >= max_retries:
                    raise
                delay = _compute_backoff_seconds(attempt, self._retry.min_delay_seconds, self._retry.max_delay_seconds)
                self._retry.on_retry and self._retry.on_retry(
                    {
                        "attempt": attempt,
                        "max_retries": max_retries,
                        "delay_seconds": delay,
                        "reason": "network_error",
                    }
                )
                await asyncio.sleep(delay)
                continue

            if not _should_retry_response(response) or attempt >= max_retries:
                return response

            retry_after = _parse_retry_after_seconds(response.headers.get("Retry-After"))
            delay = retry_after if retry_after is not None else _compute_backoff_seconds(attempt, self._retry.min_delay_seconds, self._retry.max_delay_seconds)
            delay = min(self._retry.max_delay_seconds, max(0.0, delay))

            self._retry.on_retry and self._retry.on_retry(
                {
                    "attempt": attempt,
                    "max_retries": max_retries,
                    "delay_seconds": delay,
                    "reason": "http_status",
                    "status_code": response.status_code,
                }
            )

            await response.aclose()
            await asyncio.sleep(delay)

        # Defensive: should never reach
        return await super().request(method, url, **kwargs)


def _to_uuid(value: Union[str, UUID]) -> UUID:
    """Convert string to UUID if needed."""
    if isinstance(value, str):
        return UUID(value)
    return value


def _to_unset_or_value(value: Optional[Any]) -> Union[Unset, Any]:
    """Convert None to UNSET."""
    return UNSET if value is None else value


def _to_iso_utc_str(value: Optional[Union[str, datetime]]) -> Optional[str]:
    """Convert a datetime or string to an ISO8601 UTC string.

    - If value is a string, it is returned unchanged (assumed to be ISO8601)
    - If value is a timezone-aware datetime, it is converted to UTC ISO string
    - If value is a naive datetime, it is treated as UTC and suffixed accordingly
    - If value is None, returns None
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.astimezone(timezone.utc).isoformat()
    return None



class MachinesAPI:
    """Machines API endpoints."""
    
    def __init__(self, client: AuthenticatedClient):
        self.client = client
    
    async def list(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        status: Optional[MachineStatus] = None,
        *,
        search: Optional[str] = None,
        created_at_from: Optional[Union[str, datetime]] = None,
        created_at_to: Optional[Union[str, datetime]] = None,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[PaginatedResponseWithIncludesMachineResponse]:
        """List machines with optional filtering.

        Args:
            skip: Pagination skip
            limit: Pagination limit
            status: Machine status filter
            search: Search machines by name or hostname (case-insensitive substring match)
            created_at_from: Optional start datetime (UTC or ISO string)
            created_at_to: Optional end datetime (UTC or ISO string)
            include: Optional list of related resources to include in the response.
                Available values: ["pools"].
                Related resources are returned in the `included` array following the JSON:API pattern.
        
        Returns:
            ApiResponse with PaginatedResponseWithIncludesMachineResponse. Each machine includes
            desktop parameters (machine_parameters, machine_sensitive_parameters) if configured,
            plus the current `physical_server_id` when it is connected to a WebSocket server.
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = await list_machines_v1_machines_get.asyncio(
                client=self.client,
                skip=_to_unset_or_value(skip),
                limit=_to_unset_or_value(limit),
                search=_to_unset_or_value(search),
                status=status,
                created_at_from=_to_unset_or_value(_to_iso_utc_str(created_at_from)),
                created_at_to=_to_unset_or_value(_to_iso_utc_str(created_at_to)),
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def list_sync(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        status: Optional[MachineStatus] = None,
        *,
        search: Optional[str] = None,
        created_at_from: Optional[Union[str, datetime]] = None,
        created_at_to: Optional[Union[str, datetime]] = None,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[PaginatedResponseWithIncludesMachineResponse]:
        """List machines with optional filtering (synchronous).
        
        Args:
            skip: Pagination skip
            limit: Pagination limit
            status: Machine status filter
            search: Search machines by name or hostname (case-insensitive substring match)
            created_at_from: Optional start datetime (UTC or ISO string)
            created_at_to: Optional end datetime (UTC or ISO string)
            include: Optional list of related resources to include in the response.
                Available values: ["pools"].
        
        Returns:
            ApiResponse with PaginatedResponseWithIncludesMachineResponse. Each machine includes
            desktop parameters (machine_parameters, machine_sensitive_parameters) if configured,
            plus the current `physical_server_id` when it is connected to a WebSocket server.
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = list_machines_v1_machines_get.sync(
                client=self.client,
                skip=_to_unset_or_value(skip),
                limit=_to_unset_or_value(limit),
                search=_to_unset_or_value(search),
                status=status,
                created_at_from=_to_unset_or_value(_to_iso_utc_str(created_at_from)),
                created_at_to=_to_unset_or_value(_to_iso_utc_str(created_at_to)),
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def create(self, data: MachineCreate) -> ApiResponse[MachineResponse]:
        """Create a new machine.
        
        Args:
            data: MachineCreate object with:
                - fingerprint: Unique machine fingerprint
                - unkey_key_id: API key ID for authentication
                - name: Optional machine name
                - machine_parameters: Optional dict of desktop parameters
                - machine_sensitive_parameters: Optional dict of sensitive desktop parameters
                  (provide actual values, they'll be stored in Basis Theory)
                - hostname, os_info, version: Optional machine metadata
        """
        try:
            response = await create_machine_v1_machines_post.asyncio(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def create_sync(self, data: MachineCreate) -> ApiResponse[MachineResponse]:
        """Create a new machine (synchronous).
        
        Args:
            data: MachineCreate object with:
                - fingerprint: Unique machine fingerprint
                - unkey_key_id: API key ID for authentication
                - name: Optional machine name
                - machine_parameters: Optional dict of desktop parameters
                - machine_sensitive_parameters: Optional dict of sensitive desktop parameters
                  (provide actual values, they'll be stored in Basis Theory)
                - hostname, os_info, version: Optional machine metadata
        """
        try:
            response = create_machine_v1_machines_post.sync(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def get(
        self,
        machine_id: str,
        *,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[MachineResponse]:
        """Get a specific machine by ID.
        
        Args:
            machine_id: The machine UUID
            include: Optional list of related resources to include in the response.
                Available values: ["pools"].
                Related resources are returned in the `included` array following the JSON:API pattern.
        
        Returns:
            ApiResponse with MachineResponse including:
                - Basic info: id, name, status, fingerprint, etc.
                - machine_parameters: Dict of desktop parameters (if configured)
                - machine_sensitive_parameters: Dict of sensitive parameter aliases (if configured)
                - physical_server_id: Fly machine ID currently hosting the WebSocket connection
                - pools: List of pools this machine belongs to
                - included: Related resources (when include parameter is used)
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = await get_machine_v1_machines_machine_id_get.asyncio(
                client=self.client,
                machine_id=_to_uuid(machine_id),
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def get_sync(
        self,
        machine_id: str,
        *,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[MachineResponse]:
        """Get a specific machine by ID (synchronous).
        
        Args:
            machine_id: The machine UUID
            include: Optional list of related resources to include in the response.
                Available values: ["pools"].
        
        Returns:
            ApiResponse with MachineResponse including:
                - Basic info: id, name, status, fingerprint, etc.
                - machine_parameters: Dict of desktop parameters (if configured)
                - machine_sensitive_parameters: Dict of sensitive parameter aliases (if configured)
                - physical_server_id: Fly machine ID currently hosting the WebSocket connection
                - pools: List of pools this machine belongs to
                - included: Related resources (when include parameter is used)
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = get_machine_v1_machines_machine_id_get.sync(
                client=self.client,
                machine_id=_to_uuid(machine_id),
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def update(self, machine_id: str, data: MachineUpdate) -> ApiResponse[MachineResponse]:
        """Update a machine.
        
        Args:
            machine_id: The machine ID to update
            data: MachineUpdate object with fields to update:
                - name: Optional machine name
                - machine_parameters: Optional dict of machine-specific input values that 
                  automatically populate runs on this desktop. Use {} to clear all.
                - machine_sensitive_parameters: Optional dict of sensitive parameters 
                  (provide actual values, they'll be stored in Basis Theory). Use {} to clear all.
                - status, is_available, hostname, os_info, version: Other machine fields
                - reserved_session_id: Set to null to clear reservation
        
        Desktop Parameters:
            Machine parameters automatically merge into runs assigned to this machine,
            overriding run-level input values. Use {param_name} or {$sensitive_param}
            syntax in workflow prompts.
        
        Note: 
            - linked_keepalive_machine_id is not writable; it is managed by
              Cyberdriver link events and will be set/cleared automatically by the platform.
            - physical_server_id is read-only; it is populated automatically when a machine
              connects to a WebSocket server and cleared on disconnect.
            - For machine_sensitive_parameters, provide actual secret values. They will be
              stored securely in Basis Theory and only aliases stored in the database.
        """
        try:
            response = await update_machine_v1_machines_machine_id_patch.asyncio(
                client=self.client,
                machine_id=_to_uuid(machine_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def update_sync(self, machine_id: str, data: MachineUpdate) -> ApiResponse[MachineResponse]:
        """Update a machine (synchronous).
        
        Args:
            machine_id: The machine ID to update
            data: MachineUpdate object with fields to update:
                - name: Optional machine name
                - machine_parameters: Optional dict of machine-specific input values that 
                  automatically populate runs on this desktop. Use {} to clear all.
                - machine_sensitive_parameters: Optional dict of sensitive parameters 
                  (provide actual values, they'll be stored in Basis Theory). Use {} to clear all.
                - status, is_available, hostname, os_info, version: Other machine fields
                - reserved_session_id: Set to null to clear reservation
        
        Desktop Parameters:
            Machine parameters automatically merge into runs assigned to this machine,
            overriding run-level input values. Use {param_name} or {$sensitive_param}
            syntax in workflow prompts.
        
        Note: 
            - linked_keepalive_machine_id is not writable; it is managed by
              Cyberdriver link events and will be set/cleared automatically by the platform.
            - For machine_sensitive_parameters, provide actual secret values. They will be
              stored securely in Basis Theory and only aliases stored in the database.
        """
        try:
            response = update_machine_v1_machines_machine_id_patch.sync(
                client=self.client,
                machine_id=_to_uuid(machine_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def clear_session(self, machine_id: str) -> ApiResponse[MachineResponse]:
        """Clear the machine's reserved session (cancels queued/running session runs).

        This sends reserved_session_id=null per API contract.
        """
        try:
            update = MachineUpdate(reserved_session_id=None)
            response = await update_machine_v1_machines_machine_id_patch.asyncio(
                client=self.client,
                machine_id=_to_uuid(machine_id),
                body=update
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def clear_session_sync(self, machine_id: str) -> ApiResponse[MachineResponse]:
        """Clear the machine's reserved session (synchronous)."""
        try:
            update = MachineUpdate(reserved_session_id=None)
            response = update_machine_v1_machines_machine_id_patch.sync(
                client=self.client,
                machine_id=_to_uuid(machine_id),
                body=update
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def delete(self, machine_id: str) -> ApiResponse[MachineResponse]:
        """Delete a machine.
        
        Associated runs are preserved with machine_id set to NULL to maintain run history.
        Connections and request logs are cascade deleted.
        
        If the machine has desktop sensitive parameters, they will be automatically
        cleaned up from Basis Theory before deletion.
        """
        try:
            await delete_machine_v1_machines_machine_id_delete.asyncio(
                client=self.client,
                machine_id=_to_uuid(machine_id)
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)
    
    def delete_sync(self, machine_id: str) -> ApiResponse[MachineResponse]:
        """Delete a machine (synchronous).
        
        Associated runs are preserved with machine_id set to NULL to maintain run history.
        Connections and request logs are cascade deleted.
        
        If the machine has desktop sensitive parameters, they will be automatically
        cleaned up from Basis Theory before deletion.
        """
        try:
            delete_machine_v1_machines_machine_id_delete.sync(
                client=self.client,
                machine_id=_to_uuid(machine_id)
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)
    
    async def get_pools(self, machine_id: str) -> ApiResponse[List[PoolResponse]]:
        """Get all pools that a machine belongs to."""
        try:
            response = await get_machine_pools_v1_machines_machine_id_pools_get.asyncio(
                client=self.client,
                machine_id=_to_uuid(machine_id)
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def get_pools_sync(self, machine_id: str) -> ApiResponse[List[PoolResponse]]:
        """Get all pools that a machine belongs to (synchronous)."""
        try:
            response = get_machine_pools_v1_machines_machine_id_pools_get.sync(
                client=self.client,
                machine_id=_to_uuid(machine_id)
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def update_pools(self, machine_id: str, data: MachinePoolUpdate) -> ApiResponse[List[PoolResponse]]:
        """Update a machine's pool assignments.
        
        This replaces all existing pool assignments with the new ones.
        
        Args:
            machine_id: The machine ID
            data: MachinePoolUpdate with pool_ids list
        
        Returns:
            ApiResponse with updated MachineResponse
        """
        try:
            response = await update_machine_pools_v1_machines_machine_id_pools_put.asyncio(
                client=self.client,
                machine_id=_to_uuid(machine_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def update_pools_sync(self, machine_id: str, data: MachinePoolUpdate) -> ApiResponse[List[PoolResponse]]:
        """Update a machine's pool assignments (synchronous).
        
        This replaces all existing pool assignments with the new ones.
        
        Args:
            machine_id: The machine ID
            data: MachinePoolUpdate with pool_ids list
        
        Returns:
            ApiResponse with updated MachineResponse
        """
        try:
            response = update_machine_pools_v1_machines_machine_id_pools_put.sync(
                client=self.client,
                machine_id=_to_uuid(machine_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)


class PoolsAPI:
    """Pools API endpoints."""
    
    def __init__(self, client: AuthenticatedClient):
        self.client = client
    
    async def list(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        *,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[PaginatedResponseWithIncludesPoolResponse]:
        """List pools for the organization.
        
        Args:
            skip: Pagination skip
            limit: Pagination limit
            include: Optional list of related resources to include in the response.
                Available values: ["machines"].
                Related resources are returned in the `included` array following the JSON:API pattern.
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = await list_pools_v1_pools_get.asyncio(
                client=self.client,
                skip=_to_unset_or_value(skip),
                limit=_to_unset_or_value(limit),
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def list_sync(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        *,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[PaginatedResponseWithIncludesPoolResponse]:
        """List pools for the organization (synchronous).
        
        Args:
            skip: Pagination skip
            limit: Pagination limit
            include: Optional list of related resources to include in the response.
                Available values: ["machines"].
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = list_pools_v1_pools_get.sync(
                client=self.client,
                skip=_to_unset_or_value(skip),
                limit=_to_unset_or_value(limit),
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def create(self, data: PoolCreate) -> ApiResponse[PoolResponse]:
        """Create a new pool."""
        try:
            response = await create_pool_v1_pools_post.asyncio(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def create_sync(self, data: PoolCreate) -> ApiResponse[PoolResponse]:
        """Create a new pool (synchronous)."""
        try:
            response = create_pool_v1_pools_post.sync(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def get(
        self,
        pool_id: str,
        include_machines: bool = False,
        *,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[Union[PoolResponse, PoolWithMachines]]:
        """Get a specific pool by ID.
        
        Args:
            pool_id: The pool ID
            include_machines: [Deprecated] Use include=["machines"] instead.
                Whether to include full machine details.
            include: Optional list of related resources to include in the response.
                Available values: ["machines"].
                Related resources are returned in the `included` array following the JSON:API pattern.
        
        Returns:
            ApiResponse with PoolResponse (with optional included array)
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = await get_pool_v1_pools_pool_id_get.asyncio(
                client=self.client,
                pool_id=_to_uuid(pool_id),
                include_machines=include_machines,
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def get_sync(
        self,
        pool_id: str,
        include_machines: bool = False,
        *,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[Union[PoolResponse, PoolWithMachines]]:
        """Get a specific pool by ID (synchronous).
        
        Args:
            pool_id: The pool ID
            include_machines: [Deprecated] Use include=["machines"] instead.
                Whether to include full machine details.
            include: Optional list of related resources to include in the response.
                Available values: ["machines"].
        
        Returns:
            ApiResponse with PoolResponse (with optional included array)
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = get_pool_v1_pools_pool_id_get.sync(
                client=self.client,
                pool_id=_to_uuid(pool_id),
                include_machines=include_machines,
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def update(self, pool_id: str, data: PoolUpdate) -> ApiResponse[PoolResponse]:
        """Update a pool's details."""
        try:
            response = await update_pool_v1_pools_pool_id_patch.asyncio(
                client=self.client,
                pool_id=_to_uuid(pool_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def update_sync(self, pool_id: str, data: PoolUpdate) -> ApiResponse[PoolResponse]:
        """Update a pool's details (synchronous)."""
        try:
            response = update_pool_v1_pools_pool_id_patch.sync(
                client=self.client,
                pool_id=_to_uuid(pool_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def delete(self, pool_id: str) -> ApiResponse[PoolResponse]:
        """Delete a pool. This will not delete the machines in the pool."""
        try:
            await delete_pool_v1_pools_pool_id_delete.asyncio(
                client=self.client,
                pool_id=_to_uuid(pool_id)
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)
    
    def delete_sync(self, pool_id: str) -> ApiResponse[PoolResponse]:
        """Delete a pool. This will not delete the machines in the pool (synchronous)."""
        try:
            delete_pool_v1_pools_pool_id_delete.sync(
                client=self.client,
                pool_id=_to_uuid(pool_id)
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)
    
    async def add_machines(self, pool_id: str, data: MachinePoolAssignment) -> ApiResponse[PoolWithMachines]:
        """Add machines to a pool.
        
        Args:
            pool_id: The pool ID
            data: MachinePoolAssignment with machine_ids list
        
        Returns:
            ApiResponse with PoolWithMachines
        """
        try:
            response = await add_machines_to_pool_v1_pools_pool_id_machines_post.asyncio(
                client=self.client,
                pool_id=_to_uuid(pool_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def add_machines_sync(self, pool_id: str, data: MachinePoolAssignment) -> ApiResponse[PoolWithMachines]:
        """Add machines to a pool (synchronous).
        
        Args:
            pool_id: The pool ID
            data: MachinePoolAssignment with machine_ids list
        
        Returns:
            ApiResponse with PoolWithMachines
        """
        try:
            response = add_machines_to_pool_v1_pools_pool_id_machines_post.sync(
                client=self.client,
                pool_id=_to_uuid(pool_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def remove_machines(self, pool_id: str, data: MachinePoolAssignment) -> ApiResponse[PoolWithMachines]:
        """Remove machines from a pool.
        
        Args:
            pool_id: The pool ID
            data: MachinePoolAssignment with machine_ids list
        
        Returns:
            ApiResponse with success status
        """
        try:
            await remove_machines_from_pool_v1_pools_pool_id_machines_delete.asyncio(
                client=self.client,
                pool_id=_to_uuid(pool_id),
                body=data
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)
    
    def remove_machines_sync(self, pool_id: str, data: MachinePoolAssignment) -> ApiResponse[PoolWithMachines]:
        """Remove machines from a pool (synchronous).
        
        Args:
            pool_id: The pool ID
            data: MachinePoolAssignment with machine_ids list
        
        Returns:
            ApiResponse with success status
        """
        try:
            remove_machines_from_pool_v1_pools_pool_id_machines_delete.sync(
                client=self.client,
                pool_id=_to_uuid(pool_id),
                body=data
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)


class WorkflowsAPI:
    """Workflows API endpoints."""
    
    def __init__(self, client: AuthenticatedClient):
        self.client = client
    
    async def list(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        *,
        search: Optional[str] = None,
        created_at_from: Optional[Union[str, datetime]] = None,
        created_at_to: Optional[Union[str, datetime]] = None,
        updated_at_from: Optional[Union[str, datetime]] = None,
        updated_at_to: Optional[Union[str, datetime]] = None,
        tag_ids: Optional[str] = None,
        include_tags: bool = False,
    ) -> ApiResponse[PaginatedResponseWorkflowResponse]:
        """List workflows with optional filtering.

        Args:
            skip: Pagination skip
            limit: Pagination limit
            search: Search workflows by name (case-insensitive substring match)
            created_at_from: Start datetime for created_at filter (UTC or ISO)
            created_at_to: End datetime for created_at filter (UTC or ISO)
            updated_at_from: Start datetime for updated_at filter (UTC or ISO)
            updated_at_to: End datetime for updated_at filter (UTC or ISO)
            tag_ids: Comma-separated list of tag UUIDs. Returns workflows with ALL specified tags (AND logic)
            include_tags: Include tags in the response
        """
        try:
            response = await list_workflows_v1_workflows_get.asyncio(
                client=self.client,
                skip=_to_unset_or_value(skip),
                limit=_to_unset_or_value(limit),
                search=_to_unset_or_value(search),
                created_at_from=_to_unset_or_value(_to_iso_utc_str(created_at_from)),
                created_at_to=_to_unset_or_value(_to_iso_utc_str(created_at_to)),
                updated_at_from=_to_unset_or_value(_to_iso_utc_str(updated_at_from)),
                updated_at_to=_to_unset_or_value(_to_iso_utc_str(updated_at_to)),
                tag_ids=_to_unset_or_value(tag_ids),
                include_tags=include_tags,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def list_sync(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        *,
        search: Optional[str] = None,
        created_at_from: Optional[Union[str, datetime]] = None,
        created_at_to: Optional[Union[str, datetime]] = None,
        updated_at_from: Optional[Union[str, datetime]] = None,
        updated_at_to: Optional[Union[str, datetime]] = None,
        tag_ids: Optional[str] = None,
        include_tags: bool = False,
    ) -> ApiResponse[PaginatedResponseWorkflowResponse]:
        """List workflows (synchronous) with optional filtering.

        Args:
            skip: Pagination skip
            limit: Pagination limit
            search: Search workflows by name (case-insensitive substring match)
            created_at_from: Start datetime for created_at filter (UTC or ISO)
            created_at_to: End datetime for created_at filter (UTC or ISO)
            updated_at_from: Start datetime for updated_at filter (UTC or ISO)
            updated_at_to: End datetime for updated_at filter (UTC or ISO)
            tag_ids: Comma-separated list of tag UUIDs. Returns workflows with ALL specified tags (AND logic)
            include_tags: Include tags in the response
        """
        try:
            response = list_workflows_v1_workflows_get.sync(
                client=self.client,
                skip=_to_unset_or_value(skip),
                limit=_to_unset_or_value(limit),
                search=_to_unset_or_value(search),
                created_at_from=_to_unset_or_value(_to_iso_utc_str(created_at_from)),
                created_at_to=_to_unset_or_value(_to_iso_utc_str(created_at_to)),
                updated_at_from=_to_unset_or_value(_to_iso_utc_str(updated_at_from)),
                updated_at_to=_to_unset_or_value(_to_iso_utc_str(updated_at_to)),
                tag_ids=_to_unset_or_value(tag_ids),
                include_tags=include_tags,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def create(self, data: WorkflowCreate) -> ApiResponse[WorkflowResponse]:
        """Create a new workflow."""
        try:
            response = await create_workflow_v1_workflows_post.asyncio(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def create_sync(self, data: WorkflowCreate) -> ApiResponse[WorkflowResponse]:
        """Create a new workflow (synchronous)."""
        try:
            response = create_workflow_v1_workflows_post.sync(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def get(self, workflow_id: str) -> ApiResponse[WorkflowResponse]:
        """Get a specific workflow by ID."""
        try:
            response = await get_workflow_v1_workflows_workflow_id_get.asyncio(
                client=self.client,
                workflow_id=_to_uuid(workflow_id)
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def get_sync(self, workflow_id: str) -> ApiResponse[WorkflowResponse]:
        """Get a specific workflow by ID (synchronous)."""
        try:
            response = get_workflow_v1_workflows_workflow_id_get.sync(
                client=self.client,
                workflow_id=_to_uuid(workflow_id)
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def update(self, workflow_id: str, data: WorkflowUpdate) -> ApiResponse[WorkflowResponse]:
        """Update a workflow."""
        try:
            response = await update_workflow_v1_workflows_workflow_id_patch.asyncio(
                client=self.client,
                workflow_id=_to_uuid(workflow_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def update_sync(self, workflow_id: str, data: WorkflowUpdate) -> ApiResponse[WorkflowResponse]:
        """Update a workflow (synchronous)."""
        try:
            response = update_workflow_v1_workflows_workflow_id_patch.sync(
                client=self.client,
                workflow_id=_to_uuid(workflow_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def delete(self, workflow_id: str) -> ApiResponse[WorkflowResponse]:
        """Delete a workflow."""
        try:
            await delete_workflow_v1_workflows_workflow_id_delete.asyncio(
                client=self.client,
                workflow_id=_to_uuid(workflow_id)
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)
    
    def delete_sync(self, workflow_id: str) -> ApiResponse[WorkflowResponse]:
        """Delete a workflow (synchronous)."""
        try:
            delete_workflow_v1_workflows_workflow_id_delete.sync(
                client=self.client,
                workflow_id=_to_uuid(workflow_id)
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)
    
    # -------------------------------------------------------------------------
    # Prompt Image Methods
    # -------------------------------------------------------------------------
    
    async def upload_prompt_image(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_content: Optional[bytes] = None,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> ApiResponse[WorkflowPromptImageResponse]:
        """Upload an image for use in workflow prompts.
        
        The returned supabase_url can be embedded directly in workflow prompt HTML:
        <img src="supabase://workflow-prompt-images/org_xxx/prompt-assets/my-image.png" alt="Description">
        
        Args:
            file_path: Path to an image file to upload (mutually exclusive with file_content)
            file_content: Raw bytes of the image to upload (mutually exclusive with file_path)
            filename: Optional filename (required if using file_content, otherwise derived from file_path)
            content_type: Optional MIME type (e.g., "image/png"). Auto-detected if not provided.
        
        Returns:
            ApiResponse containing the WorkflowPromptImageResponse with supabase_url and signed_url
        """
        try:
            if file_path and file_content:
                raise ValueError("Provide either file_path or file_content, not both")
            if not file_path and not file_content:
                raise ValueError("Must provide either file_path or file_content")
            
            if file_path:
                path = Path(file_path)
                with open(path, "rb") as f:
                    content = f.read()
                fname = filename or path.name
            else:
                content = file_content
                fname = filename or "image"
            
            # Auto-detect content type from extension if not provided
            if not content_type:
                ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
                content_type_map = {
                    "png": "image/png",
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "gif": "image/gif",
                    "webp": "image/webp",
                }
                content_type = content_type_map.get(ext, "application/octet-stream")
            
            from io import BytesIO
            file_obj = OpenAPIFile(payload=BytesIO(content), file_name=fname, mime_type=content_type)
            body = BodyUploadWorkflowPromptImageV1WorkflowsPromptImagePost(file=file_obj)
            
            response = await upload_workflow_prompt_image_v1_workflows_prompt_image_post.asyncio(
                client=self.client,
                body=body,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def upload_prompt_image_sync(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_content: Optional[bytes] = None,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> ApiResponse[WorkflowPromptImageResponse]:
        """Upload an image for use in workflow prompts (synchronous).
        
        See upload_prompt_image for full documentation.
        """
        try:
            if file_path and file_content:
                raise ValueError("Provide either file_path or file_content, not both")
            if not file_path and not file_content:
                raise ValueError("Must provide either file_path or file_content")
            
            if file_path:
                path = Path(file_path)
                with open(path, "rb") as f:
                    content = f.read()
                fname = filename or path.name
            else:
                content = file_content
                fname = filename or "image"
            
            if not content_type:
                ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
                content_type_map = {
                    "png": "image/png",
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "gif": "image/gif",
                    "webp": "image/webp",
                }
                content_type = content_type_map.get(ext, "application/octet-stream")
            
            from io import BytesIO
            file_obj = OpenAPIFile(payload=BytesIO(content), file_name=fname, mime_type=content_type)
            body = BodyUploadWorkflowPromptImageV1WorkflowsPromptImagePost(file=file_obj)
            
            response = upload_workflow_prompt_image_v1_workflows_prompt_image_post.sync(
                client=self.client,
                body=body,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def list_prompt_images(self) -> ApiResponse[List[WorkflowPromptImageListItem]]:
        """List all workflow prompt images for the organization."""
        try:
            response = await list_workflow_prompt_images_v1_workflows_prompt_images_get.asyncio(
                client=self.client,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def list_prompt_images_sync(self) -> ApiResponse[List[WorkflowPromptImageListItem]]:
        """List all workflow prompt images for the organization (synchronous)."""
        try:
            response = list_workflow_prompt_images_v1_workflows_prompt_images_get.sync(
                client=self.client,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def get_prompt_image_signed_url(self, path: str) -> ApiResponse[WorkflowPromptImageSignedUrlResponse]:
        """Get a fresh signed URL for an existing workflow prompt image.
        
        Args:
            path: The storage path of the image (e.g., "org_xxx/prompt-assets/image.png")
        
        Returns:
            ApiResponse containing the signed URL and expiration info
        """
        try:
            response = await get_workflow_prompt_image_signed_url_v1_workflows_prompt_image_signed_url_get.asyncio(
                client=self.client,
                path=path,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def get_prompt_image_signed_url_sync(self, path: str) -> ApiResponse[WorkflowPromptImageSignedUrlResponse]:
        """Get a fresh signed URL for an existing workflow prompt image (synchronous)."""
        try:
            response = get_workflow_prompt_image_signed_url_v1_workflows_prompt_image_signed_url_get.sync(
                client=self.client,
                path=path,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def delete_prompt_image(self, path: str) -> ApiResponse[Dict[str, Any]]:
        """Delete a workflow prompt image.
        
        Args:
            path: The storage path of the image to delete
        
        Returns:
            ApiResponse with success status
        """
        try:
            await delete_workflow_prompt_image_v1_workflows_prompt_image_delete.asyncio(
                client=self.client,
                path=path,
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)
    
    def delete_prompt_image_sync(self, path: str) -> ApiResponse[Dict[str, Any]]:
        """Delete a workflow prompt image (synchronous)."""
        try:
            delete_workflow_prompt_image_v1_workflows_prompt_image_delete.sync(
                client=self.client,
                path=path,
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)


class RunsAPI:
    """Runs API endpoints."""
    
    def __init__(self, client: AuthenticatedClient):
        self.client = client
    
    async def list(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        status: Optional[RunStatus] = None,
        workflow_id: Optional[str] = None,
        machine_id: Optional[str] = None,
        session_id: Optional[str] = None,
        *,
        created_at_from: Optional[Union[str, datetime]] = None,
        created_at_to: Optional[Union[str, datetime]] = None,
        search: Optional[str] = None,
        deep_search: bool = False,
        fields: Optional[List[RunField]] = None,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[PaginatedResponseWithIncludesRunResponse]:
        """List runs with optional filtering.

        Runs are ordered by: RUNNING (by started_at DESC) first, then all others (by ended_at DESC).
        This surfaces active work and recent completions.

        Args:
            skip: Pagination skip
            limit: Pagination limit
            status: Run status filter
            workflow_id: Filter by workflow ID
            machine_id: Filter by machine ID
            session_id: Filter by session ID
            created_at_from: Optional start datetime (UTC or ISO string)
            created_at_to: Optional end datetime (UTC or ISO string)
            search: Search runs by input_values, output_data, error, session_alias (case-insensitive)
            deep_search: If True, also search run_message_history (slower but more comprehensive)
            fields: Optional list of fields to include per run (projection). When set,
                the response includes only these plus base fields (id, workflow_id,
                machine_id, status, created_at). Available fields include: started_at,
                ended_at, error, output_data, input_values, usage_metadata, and more.
            include: Optional list of related resources to include in the response.
                Available values: ["workflow", "machine", "machine.pools"].
                Related resources are returned in the `included` array following the JSON:API pattern.
        
        Returns:
            ApiResponse with RunResponse objects including timing fields:
                - created_at: When run was created
                - started_at: When run execution started (null for SCHEDULING runs)
                - ended_at: When run completed (null for RUNNING/SCHEDULING runs)
                - included: Related resources (when include parameter is used)
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = await list_runs_v1_runs_get.asyncio(
                client=self.client,
                skip=_to_unset_or_value(skip),
                limit=_to_unset_or_value(limit),
                status=status,
                workflow_id=_to_uuid(workflow_id) if workflow_id else UNSET,
                machine_id=_to_uuid(machine_id) if machine_id else UNSET,
                session_id=_to_uuid(session_id) if session_id else UNSET,
                created_at_from=_to_unset_or_value(_to_iso_utc_str(created_at_from)),
                created_at_to=_to_unset_or_value(_to_iso_utc_str(created_at_to)),
                search=_to_unset_or_value(search),
                deep_search=deep_search,
                fields=_to_unset_or_value(fields),
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def list_sync(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        status: Optional[RunStatus] = None,
        workflow_id: Optional[str] = None,
        machine_id: Optional[str] = None,
        session_id: Optional[str] = None,
        *,
        created_at_from: Optional[Union[str, datetime]] = None,
        created_at_to: Optional[Union[str, datetime]] = None,
        search: Optional[str] = None,
        deep_search: bool = False,
        fields: Optional[List[RunField]] = None,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[PaginatedResponseWithIncludesRunResponse]:
        """List runs with optional filtering (synchronous).

        See async variant for parameter docs. Supports `fields` projection, `include`, and `search`.
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = list_runs_v1_runs_get.sync(
                client=self.client,
                skip=_to_unset_or_value(skip),
                limit=_to_unset_or_value(limit),
                status=status,
                workflow_id=_to_uuid(workflow_id) if workflow_id else UNSET,
                machine_id=_to_uuid(machine_id) if machine_id else UNSET,
                session_id=_to_uuid(session_id) if session_id else UNSET,
                created_at_from=_to_unset_or_value(_to_iso_utc_str(created_at_from)),
                created_at_to=_to_unset_or_value(_to_iso_utc_str(created_at_to)),
                search=_to_unset_or_value(search),
                deep_search=deep_search,
                fields=_to_unset_or_value(fields),
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)

    async def retry(self, run_id: str, retry: RunRetry) -> ApiResponse[RunResponse]:
        """Retry an existing run in-place (same run_id).

        Clears previous outputs/history/output attachments, optionally replaces inputs/files,
        and attempts immediate assignment unless the session is busy.
        """
        try:
            response = await retry_run_v1_runs_run_id_retry_post.asyncio(
                client=self.client,
                run_id=_to_uuid(run_id),
                body=retry,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)

    def retry_sync(self, run_id: str, retry: RunRetry) -> ApiResponse[RunResponse]:
        """Retry an existing run in-place (synchronous)."""
        try:
            response = retry_run_v1_runs_run_id_retry_post.sync(
                client=self.client,
                run_id=_to_uuid(run_id),
                body=retry,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def create(self, data: RunCreate) -> ApiResponse[RunResponse]:
        """Create a new run.
        
        Args:
            data: RunCreate object with:
                - workflow_id: The workflow to run
                - machine_id: Optional specific machine ID
                - pool_ids: Optional list of pool IDs (machine must be in ALL specified pools)
                - input_values: Optional input values for workflow variables
                - file_inputs: Optional files to upload to the machine
                - sensitive_input_values: Optional sensitive inputs (stored securely, not in DB)
                - session_id: Optional UUID to join an existing session
                - start_session: Optional bool to start a new machine session
                - session_alias: Optional alias to persist outputs for refs in this session
                - release_session_after: Optional bool to release the session when this run completes (success, error, or cancel)
        
        Returns:
            ApiResponse with RunResponse
        """
        try:
            response = await create_run_v1_runs_post.asyncio(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def create_sync(self, data: RunCreate) -> ApiResponse[RunResponse]:
        """Create a new run (synchronous).
        
        Args:
            data: RunCreate object with:
                - workflow_id: The workflow to run
                - machine_id: Optional specific machine ID
                - pool_ids: Optional list of pool IDs (machine must be in ALL specified pools)
                - input_values: Optional input values for workflow variables
                - file_inputs: Optional files to upload to the machine
                - sensitive_input_values: Optional sensitive inputs (stored securely, not in DB)
                - session_id: Optional UUID to join an existing session
                - start_session: Optional bool to start a new machine session
                - session_alias: Optional alias to persist outputs for refs in this session
                - release_session_after: Optional bool to release the session when this run completes (success, error, or cancel)
        
        Returns:
            ApiResponse with RunResponse
        """
        try:
            response = create_run_v1_runs_post.sync(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def get(
        self,
        run_id: str,
        *,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[RunResponse]:
        """Get a specific run by ID.
        
        Args:
            run_id: The run UUID
            include: Optional list of related resources to include in the response.
                Available values: ["workflow", "machine", "machine.pools"].
                Related resources are returned in the `included` array following the JSON:API pattern.
        
        Returns:
            ApiResponse with RunResponse including timing information:
                - created_at: When run was created
                - started_at: When run execution started (null if not started)
                - ended_at: When run completed (null if not finished)
                - included: Related resources (when include parameter is used)
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = await get_run_v1_runs_run_id_get.asyncio(
                client=self.client,
                run_id=_to_uuid(run_id),
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def get_sync(
        self,
        run_id: str,
        *,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[RunResponse]:
        """Get a specific run by ID (synchronous).
        
        Args:
            run_id: The run UUID
            include: Optional list of related resources to include in the response.
                Available values: ["workflow", "machine", "machine.pools"].
        
        Returns:
            ApiResponse with RunResponse including timing information:
                - created_at: When run was created
                - started_at: When run execution started (null if not started)
                - ended_at: When run completed (null if not finished)
                - included: Related resources (when include parameter is used)
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = get_run_v1_runs_run_id_get.sync(
                client=self.client,
                run_id=_to_uuid(run_id),
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def update(self, run_id: str, data: RunUpdate) -> ApiResponse[RunResponse]:
        """Update a run.

        Notes:
            This supports updating flexible per-run usage/billing metadata via `usage_metadata`
            (if your server supports it).
        """
        try:
            response = await update_run_v1_runs_run_id_patch.asyncio(
                client=self.client,
                run_id=_to_uuid(run_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def update_sync(self, run_id: str, data: RunUpdate) -> ApiResponse[RunResponse]:
        """Update a run (synchronous)."""
        try:
            response = update_run_v1_runs_run_id_patch.sync(
                client=self.client,
                run_id=_to_uuid(run_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def delete(self, run_id: str) -> ApiResponse[RunResponse]:
        """Delete a run."""
        try:
            await delete_run_v1_runs_run_id_delete.asyncio(
                client=self.client,
                run_id=_to_uuid(run_id)
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)
    
    def delete_sync(self, run_id: str) -> ApiResponse[RunResponse]:
        """Delete a run (synchronous)."""
        try:
            delete_run_v1_runs_run_id_delete.sync(
                client=self.client,
                run_id=_to_uuid(run_id)
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)
    
    async def bulk_create(self, data: RunBulkCreate) -> ApiResponse[RunBulkCreateResponse]:
        """Create multiple runs with the same configuration.
        
        This method efficiently creates multiple runs:
        - All runs are created in a single database transaction
        - Temporal workflows are started asynchronously 
        - Returns immediately with created run details
        
        Args:
            data: RunBulkCreate object containing:
                - workflow_id: The workflow to run
                - machine_id: Optional specific machine ID 
                - pool_ids: Optional list of pool IDs (machine must be in ALL specified pools)
                - input_values: Optional input values for workflow variables
                - file_inputs: Optional files to upload to the machine
                - sensitive_input_values: Optional sensitive inputs (stored securely, not in DB)
                - count: Number of runs to create (max 1000)
                - session_id: Optional UUID to join an existing session for all runs
                - start_session: Optional bool to start a new machine session for all runs
        
        Returns:
            ApiResponse with RunBulkCreateResponse containing:
                - created_runs: List of created RunResponse objects
                - failed_count: Number of runs that failed to create
                - errors: List of error messages for failed runs
        """
        try:
            response = await bulk_create_runs_v1_runs_bulk_post.asyncio(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def bulk_create_sync(self, data: RunBulkCreate) -> ApiResponse[RunBulkCreateResponse]:
        """Create multiple runs with the same configuration (synchronous).
        
        This method efficiently creates multiple runs:
        - All runs are created in a single database transaction
        - Temporal workflows are started asynchronously 
        - Returns immediately with created run details
        
        Args:
            data: RunBulkCreate object containing:
                - workflow_id: The workflow to run
                - machine_id: Optional specific machine ID 
                - pool_ids: Optional list of pool IDs (machine must be in ALL specified pools)
                - input_values: Optional input values for workflow variables
                - file_inputs: Optional files to upload to the machine
                - sensitive_input_values: Optional sensitive inputs (stored securely, not in DB)
                - count: Number of runs to create (max 1000)
                - session_id: Optional UUID to join an existing session for all runs
                - start_session: Optional bool to start a new machine session for all runs
        
        Returns:
            ApiResponse with RunBulkCreateResponse containing:
                - created_runs: List of created RunResponse objects
                - failed_count: Number of runs that failed to create
                - errors: List of error messages for failed runs
        """
        try:
            response = bulk_create_runs_v1_runs_bulk_post.sync(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)

    async def chain(self, data: WorkflowChainCreate) -> ApiResponse[WorkflowChainResponse]:
        """Create a multi-step chain that runs on a single reserved session/machine.

        Args:
            data: WorkflowChainCreate with steps (session_alias, inputs, sensitive_inputs),
                  optional shared_inputs/sensitive/file_inputs, and optional
                  session_id or machine_id/pool_ids for session start.

        Returns:
            ApiResponse with WorkflowChainResponse
        """
        try:
            response = await create_run_chain_v1_runs_chain_post.asyncio(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)

    def chain_sync(self, data: WorkflowChainCreate) -> ApiResponse[WorkflowChainResponse]:
        """Create a multi-step chain (synchronous).

        Args:
            data: WorkflowChainCreate with steps (session_alias, inputs, sensitive_inputs),
                  optional shared_inputs/sensitive/file_inputs, and optional
                  session_id or machine_id/pool_ids for session start.

        Returns:
            ApiResponse with WorkflowChainResponse
        """
        try:
            response = create_run_chain_v1_runs_chain_post.sync(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)


class ConnectionsAPI:
    """Connections API endpoints."""
    
    def __init__(self, client: AuthenticatedClient):
        self.client = client
    
    async def list(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        machine_id: Optional[str] = None,
        status: Optional[Union[str, ConnectionStatus]] = None
    ) -> ApiResponse[PaginatedResponseConnectionResponse]:
        """List connections with optional filtering."""
        try:
            # Handle status conversion
            if isinstance(status, str):
                status = Unset if status is None else ConnectionStatus(status)
            
            response = await list_connections_v1_connections_get.asyncio(
                client=self.client,
                skip=_to_unset_or_value(skip),
                limit=_to_unset_or_value(limit),
                machine_id=_to_uuid(machine_id) if machine_id else UNSET,
                status=status
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def list_sync(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        machine_id: Optional[str] = None,
        status: Optional[Union[str, ConnectionStatus]] = None
    ) -> ApiResponse[PaginatedResponseConnectionResponse]:
        """List connections with optional filtering (synchronous)."""
        try:
            # Handle status conversion
            if isinstance(status, str):
                status = Unset if status is None else ConnectionStatus(status)
            
            response = list_connections_v1_connections_get.sync(
                client=self.client,
                skip=_to_unset_or_value(skip),
                limit=_to_unset_or_value(limit),
                machine_id=_to_uuid(machine_id) if machine_id else UNSET,
                status=status
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def create(self, data: ConnectionCreate) -> ApiResponse[ConnectionResponse]:
        """Create a new connection."""
        try:
            response = await create_connection_v1_connections_post.asyncio(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def create_sync(self, data: ConnectionCreate) -> ApiResponse[ConnectionResponse]:
        """Create a new connection (synchronous)."""
        try:
            response = create_connection_v1_connections_post.sync(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)


class TrajectoriesAPI:
    """Trajectories API endpoints."""
    
    def __init__(self, client: AuthenticatedClient):
        self.client = client
    
    async def list(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        workflow_id: Optional[str] = None,
        is_approved: Optional[bool] = None,
        *,
        search: Optional[str] = None,
        created_at_from: Optional[Union[str, datetime]] = None,
        created_at_to: Optional[Union[str, datetime]] = None,
        updated_at_from: Optional[Union[str, datetime]] = None,
        updated_at_to: Optional[Union[str, datetime]] = None,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[PaginatedResponseWithIncludesTrajectoryResponse]:
        """List trajectories with optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Number of records to return
            workflow_id: Filter by workflow ID
            is_approved: Filter by approval status (True=approved, False=not approved, None=all)
            search: Search trajectories by name or description (case-insensitive substring match)
            created_at_from: Filter created at or after (UTC or ISO string)
            created_at_to: Filter created at or before (UTC or ISO string)
            updated_at_from: Filter updated at or after (UTC or ISO string)
            updated_at_to: Filter updated at or before (UTC or ISO string)
            include: Optional list of related resources to include in the response.
                Available values: ["workflow"].
                Related resources are returned in the `included` array following the JSON:API pattern.
        
        Note: By default returns both approved and unapproved trajectories.
        Only approved trajectories are used during workflow execution.
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = await list_trajectories_v1_trajectories_get.asyncio(
                client=self.client,
                skip=_to_unset_or_value(skip),
                limit=_to_unset_or_value(limit),
                search=_to_unset_or_value(search),
                workflow_id=_to_uuid(workflow_id) if workflow_id else UNSET,
                is_approved=_to_unset_or_value(is_approved),
                created_at_from=_to_unset_or_value(_to_iso_utc_str(created_at_from)),
                created_at_to=_to_unset_or_value(_to_iso_utc_str(created_at_to)),
                updated_at_from=_to_unset_or_value(_to_iso_utc_str(updated_at_from)),
                updated_at_to=_to_unset_or_value(_to_iso_utc_str(updated_at_to)),
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def list_sync(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        workflow_id: Optional[str] = None,
        is_approved: Optional[bool] = None,
        *,
        search: Optional[str] = None,
        created_at_from: Optional[Union[str, datetime]] = None,
        created_at_to: Optional[Union[str, datetime]] = None,
        updated_at_from: Optional[Union[str, datetime]] = None,
        updated_at_to: Optional[Union[str, datetime]] = None,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[PaginatedResponseWithIncludesTrajectoryResponse]:
        """List trajectories with optional filtering (synchronous).
        
        Args:
            skip: Number of records to skip
            limit: Number of records to return
            workflow_id: Filter by workflow ID
            is_approved: Filter by approval status (True=approved, False=not approved, None=all)
            search: Search trajectories by name or description (case-insensitive substring match)
            created_at_from: Filter created at or after (UTC or ISO string)
            created_at_to: Filter created at or before (UTC or ISO string)
            updated_at_from: Filter updated at or after (UTC or ISO string)
            updated_at_to: Filter updated at or before (UTC or ISO string)
            include: Optional list of related resources to include in the response.
                Available values: ["workflow"].
        
        Note: By default returns both approved and unapproved trajectories.
        Only approved trajectories are used during workflow execution.
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = list_trajectories_v1_trajectories_get.sync(
                client=self.client,
                skip=_to_unset_or_value(skip),
                limit=_to_unset_or_value(limit),
                search=_to_unset_or_value(search),
                workflow_id=_to_uuid(workflow_id) if workflow_id else UNSET,
                is_approved=_to_unset_or_value(is_approved),
                created_at_from=_to_unset_or_value(_to_iso_utc_str(created_at_from)),
                created_at_to=_to_unset_or_value(_to_iso_utc_str(created_at_to)),
                updated_at_from=_to_unset_or_value(_to_iso_utc_str(updated_at_from)),
                updated_at_to=_to_unset_or_value(_to_iso_utc_str(updated_at_to)),
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def create(self, data: TrajectoryCreate) -> ApiResponse[TrajectoryResponse]:
        """Create a new trajectory.
        
        Note: Trajectories are created with is_approved=False by default.
        You must explicitly approve them before they can be used during workflow execution.
        """
        try:
            response = await create_trajectory_v1_trajectories_post.asyncio(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def create_sync(self, data: TrajectoryCreate) -> ApiResponse[TrajectoryResponse]:
        """Create a new trajectory (synchronous).
        
        Note: Trajectories are created with is_approved=False by default.
        You must explicitly approve them before they can be used during workflow execution.
        """
        try:
            response = create_trajectory_v1_trajectories_post.sync(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def get(
        self,
        trajectory_id: str,
        *,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[TrajectoryResponse]:
        """Get a specific trajectory by ID.
        
        Args:
            trajectory_id: The trajectory UUID
            include: Optional list of related resources to include in the response.
                Available values: ["workflow"].
                Related resources are returned in the `included` array following the JSON:API pattern.
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = await get_trajectory_v1_trajectories_trajectory_id_get.asyncio(
                client=self.client,
                trajectory_id=_to_uuid(trajectory_id),
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def get_sync(
        self,
        trajectory_id: str,
        *,
        include: Optional[List[str]] = None,
    ) -> ApiResponse[TrajectoryResponse]:
        """Get a specific trajectory by ID (synchronous).
        
        Args:
            trajectory_id: The trajectory UUID
            include: Optional list of related resources to include in the response.
                Available values: ["workflow"].
        """
        try:
            # Convert include list to comma-separated string
            include_str = ",".join(include) if include else None
            response = get_trajectory_v1_trajectories_trajectory_id_get.sync(
                client=self.client,
                trajectory_id=_to_uuid(trajectory_id),
                include=_to_unset_or_value(include_str),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def update(self, trajectory_id: str, data: TrajectoryUpdate) -> ApiResponse[TrajectoryResponse]:
        """Update a trajectory.
        
        You can update trajectory metadata (name, description), trajectory data (steps),
        and approval status (is_approved). Only approved trajectories are used during
        workflow execution.
        """
        try:
            response = await update_trajectory_v1_trajectories_trajectory_id_patch.asyncio(
                client=self.client,
                trajectory_id=_to_uuid(trajectory_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def update_sync(self, trajectory_id: str, data: TrajectoryUpdate) -> ApiResponse[TrajectoryResponse]:
        """Update a trajectory (synchronous).
        
        You can update trajectory metadata (name, description), trajectory data (steps),
        and approval status (is_approved). Only approved trajectories are used during
        workflow execution.
        """
        try:
            response = update_trajectory_v1_trajectories_trajectory_id_patch.sync(
                client=self.client,
                trajectory_id=_to_uuid(trajectory_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def delete(self, trajectory_id: str) -> ApiResponse[TrajectoryResponse]:
        """Delete a trajectory."""
        try:
            await delete_trajectory_v1_trajectories_trajectory_id_delete.asyncio(
                client=self.client,
                trajectory_id=_to_uuid(trajectory_id)
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)
    
    def delete_sync(self, trajectory_id: str) -> ApiResponse[TrajectoryResponse]:
        """Delete a trajectory (synchronous)."""
        try:
            delete_trajectory_v1_trajectories_trajectory_id_delete.sync(
                client=self.client,
                trajectory_id=_to_uuid(trajectory_id)
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)
    
    async def get_latest_for_workflow(self, workflow_id: str) -> ApiResponse[TrajectoryResponse]:
        """Get the latest trajectory for a workflow."""
        try:
            response = await get_latest_trajectory_for_workflow_v1_workflows_workflow_id_latest_trajectory_get.asyncio(
                client=self.client,
                workflow_id=_to_uuid(workflow_id)
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def get_latest_for_workflow_sync(self, workflow_id: str) -> ApiResponse[TrajectoryResponse]:
        """Get the latest trajectory for a workflow (synchronous)."""
        try:
            response = get_latest_trajectory_for_workflow_v1_workflows_workflow_id_latest_trajectory_get.sync(
                client=self.client,
                workflow_id=_to_uuid(workflow_id)
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def duplicate(self, trajectory_id: str) -> ApiResponse[TrajectoryResponse]:
        """Duplicate a trajectory with fresh copies of all images.
        
        Creates a new trajectory with the same data as the source, but with
        all images copied to new paths in storage (copy-on-write semantics).
        The new trajectory starts unapproved and gets a name like "Original Name (Copy)".
        
        Args:
            trajectory_id: The ID of the trajectory to duplicate
            
        Returns:
            The duplicated trajectory
        """
        try:
            response = await duplicate_trajectory_v1_trajectories_trajectory_id_duplicate_post.asyncio(
                client=self.client,
                trajectory_id=_to_uuid(trajectory_id)
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def duplicate_sync(self, trajectory_id: str) -> ApiResponse[TrajectoryResponse]:
        """Duplicate a trajectory with fresh copies of all images (synchronous).
        
        Creates a new trajectory with the same data as the source, but with
        all images copied to new paths in storage (copy-on-write semantics).
        The new trajectory starts unapproved and gets a name like "Original Name (Copy)".
        
        Args:
            trajectory_id: The ID of the trajectory to duplicate
            
        Returns:
            The duplicated trajectory
        """
        try:
            response = duplicate_trajectory_v1_trajectories_trajectory_id_duplicate_post.sync(
                client=self.client,
                trajectory_id=_to_uuid(trajectory_id)
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)


class RunAttachmentsAPI:
    """Run Attachments API endpoints."""
    
    def __init__(self, client: AuthenticatedClient):
        self.client = client
    
    async def list(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        run_id: Optional[str] = None,
        attachment_type: Optional[AttachmentType] = None
    ) -> ApiResponse[PaginatedResponseRunAttachmentResponse]:
        """List run attachments with optional filtering."""
        try:
            response = await list_run_attachments_v1_run_attachments_get.asyncio(
                client=self.client,
                skip=_to_unset_or_value(skip),
                limit=_to_unset_or_value(limit),
                run_id=_to_uuid(run_id) if run_id else UNSET,
                attachment_type=attachment_type
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def list_sync(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        run_id: Optional[str] = None,
        attachment_type: Optional[AttachmentType] = None
    ) -> ApiResponse[PaginatedResponseRunAttachmentResponse]:
        """List run attachments with optional filtering (synchronous)."""
        try:
            response = list_run_attachments_v1_run_attachments_get.sync(
                client=self.client,
                skip=_to_unset_or_value(skip),
                limit=_to_unset_or_value(limit),
                run_id=_to_uuid(run_id) if run_id else UNSET,
                attachment_type=attachment_type
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def create(self, data: RunAttachmentCreate) -> ApiResponse[RunAttachmentResponse]:
        """Create a new run attachment."""
        try:
            response = await create_run_attachment_v1_run_attachments_post.asyncio(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def create_sync(self, data: RunAttachmentCreate) -> ApiResponse[RunAttachmentResponse]:
        """Create a new run attachment (synchronous)."""
        try:
            response = create_run_attachment_v1_run_attachments_post.sync(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def get(self, attachment_id: str) -> ApiResponse[RunAttachmentResponse]:
        """Get a specific run attachment by ID."""
        try:
            response = await get_run_attachment_v1_run_attachments_attachment_id_get.asyncio(
                client=self.client,
                attachment_id=_to_uuid(attachment_id)
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def get_sync(self, attachment_id: str) -> ApiResponse[RunAttachmentResponse]:
        """Get a specific run attachment by ID (synchronous)."""
        try:
            response = get_run_attachment_v1_run_attachments_attachment_id_get.sync(
                client=self.client,
                attachment_id=_to_uuid(attachment_id)
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def get_download_url(
        self, 
        attachment_id: str,
        expires_in: Optional[int] = None
    ) -> ApiResponse[RunAttachmentDownloadUrlResponse]:
        """Get a signed download URL for a run attachment.
        
        The returned URL will trigger an automatic download when accessed in a browser.
        
        Args:
            attachment_id: The ID of the attachment
            expires_in: URL expiration time in seconds (10-3600). Default: 300 (5 minutes)
        
        Returns:
            ApiResponse with RunAttachmentDownloadUrlResponse containing:
                - url: The signed download URL
                - expires_in: The expiration time in seconds
        """
        try:
            response = await get_run_attachment_download_url_v1_run_attachments_attachment_id_download_url_get.asyncio(
                client=self.client,
                attachment_id=_to_uuid(attachment_id),
                expires_in=_to_unset_or_value(expires_in)
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def get_download_url_sync(
        self, 
        attachment_id: str,
        expires_in: Optional[int] = None
    ) -> ApiResponse[RunAttachmentDownloadUrlResponse]:
        """Get a signed download URL for a run attachment (synchronous).
        
        The returned URL will trigger an automatic download when accessed in a browser.
        
        Args:
            attachment_id: The ID of the attachment
            expires_in: URL expiration time in seconds (10-3600). Default: 300 (5 minutes)
        
        Returns:
            ApiResponse with RunAttachmentDownloadUrlResponse containing:
                - url: The signed download URL
                - expires_in: The expiration time in seconds
        """
        try:
            response = get_run_attachment_download_url_v1_run_attachments_attachment_id_download_url_get.sync(
                client=self.client,
                attachment_id=_to_uuid(attachment_id),
                expires_in=_to_unset_or_value(expires_in)
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def download(self, attachment_id: str) -> ApiResponse[bytes]:
        """Download a run attachment file directly.
        
        This method returns the raw file content as bytes. For a download URL instead,
        use get_download_url().
        
        Args:
            attachment_id: The ID of the attachment to download
        
        Returns:
            ApiResponse with data containing the raw file bytes
        """
        try:
            response = await download_run_attachment_v1_run_attachments_attachment_id_download_get.asyncio(
                client=self.client,
                attachment_id=_to_uuid(attachment_id)
            )
            # Extract bytes from File object returned by generator
            if response and hasattr(response, 'payload'):
                file_bytes = response.payload.read()
                return ApiResponse(data=file_bytes)
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def download_sync(self, attachment_id: str) -> ApiResponse[bytes]:
        """Download a run attachment file directly (synchronous).
        
        This method returns the raw file content as bytes. For a download URL instead,
        use get_download_url_sync().
        
        Args:
            attachment_id: The ID of the attachment to download
        
        Returns:
            ApiResponse with data containing the raw file bytes
        """
        try:
            response = download_run_attachment_v1_run_attachments_attachment_id_download_get.sync(
                client=self.client,
                attachment_id=_to_uuid(attachment_id)
            )
            # Extract bytes from File object returned by generator
            if response and hasattr(response, 'payload'):
                file_bytes = response.payload.read()
                return ApiResponse(data=file_bytes)
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def update(self, attachment_id: str, data: RunAttachmentUpdate) -> ApiResponse[RunAttachmentResponse]:
        """Update a run attachment (e.g., set expiration)."""
        try:
            response = await update_run_attachment_v1_run_attachments_attachment_id_put.asyncio(
                client=self.client,
                attachment_id=_to_uuid(attachment_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def update_sync(self, attachment_id: str, data: RunAttachmentUpdate) -> ApiResponse[RunAttachmentResponse]:
        """Update a run attachment (e.g., set expiration) (synchronous)."""
        try:
            response = update_run_attachment_v1_run_attachments_attachment_id_put.sync(
                client=self.client,
                attachment_id=_to_uuid(attachment_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def delete(self, attachment_id: str) -> ApiResponse[RunAttachmentResponse]:
        """Delete a run attachment."""
        try:
            await delete_run_attachment_v1_run_attachments_attachment_id_delete.asyncio(
                client=self.client,
                attachment_id=_to_uuid(attachment_id)
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)
    
    def delete_sync(self, attachment_id: str) -> ApiResponse[RunAttachmentResponse]:
        """Delete a run attachment (synchronous)."""
        try:
            delete_run_attachment_v1_run_attachments_attachment_id_delete.sync(
                client=self.client,
                attachment_id=_to_uuid(attachment_id)
            )
            return ApiResponse(data={"success": True})
        except Exception as e:
            return ApiResponse(error=e)
    
    async def save_to_file(
        self,
        attachment_id: str,
        output_path: Optional[Union[str, Path]] = None,
        use_original_filename: bool = True
    ) -> ApiResponse[Dict[str, Any]]:
        """Download and save a run attachment to a file.
        
        This is a convenience method that combines getting attachment info
        and downloading the file content.
        
        Args:
            attachment_id: The ID of the attachment to download
            output_path: Path where to save the file. If None and use_original_filename
                        is True, saves to current directory with original filename.
            use_original_filename: If True and output_path is a directory, uses the
                                 attachment's original filename.
        
        Returns:
            ApiResponse with data containing the saved file path
        """
        try:
            # Get attachment info for filename
            info_response = await self.get(attachment_id)
            if info_response.error:
                return info_response
            
            attachment_info = info_response.data
            
            # Download the file content
            download_response = await self.download(attachment_id)
            if download_response.error:
                return download_response
            
            # Determine output path
            if output_path is None:
                output_path = Path(attachment_info.filename)
            else:
                output_path = Path(output_path)
                if output_path.is_dir() and use_original_filename:
                    output_path = output_path / attachment_info.filename
            
            # Save to file
            output_path.write_bytes(download_response.data)
            
            return ApiResponse(data={"path": str(output_path), "size": len(download_response.data)})
        except Exception as e:
            return ApiResponse(error=e)
    
    def save_to_file_sync(
        self,
        attachment_id: str,
        output_path: Optional[Union[str, Path]] = None,
        use_original_filename: bool = True
    ) -> ApiResponse[Dict[str, Any]]:
        """Download and save a run attachment to a file (synchronous).
        
        This is a convenience method that combines getting attachment info
        and downloading the file content.
        
        Args:
            attachment_id: The ID of the attachment to download
            output_path: Path where to save the file. If None and use_original_filename
                        is True, saves to current directory with original filename.
            use_original_filename: If True and output_path is a directory, uses the
                                 attachment's original filename.
        
        Returns:
            ApiResponse with data containing the saved file path
        """
        try:
            # Get attachment info for filename
            info_response = self.get_sync(attachment_id)
            if info_response.error:
                return info_response
            
            attachment_info = info_response.data
            
            # Download the file content
            download_response = self.download_sync(attachment_id)
            if download_response.error:
                return download_response
            
            # Determine output path
            if output_path is None:
                output_path = Path(attachment_info.filename)
            else:
                output_path = Path(output_path)
                if output_path.is_dir() and use_original_filename:
                    output_path = output_path / attachment_info.filename
            
            # Save to file
            output_path.write_bytes(download_response.data)
            
            return ApiResponse(data={"path": str(output_path), "size": len(download_response.data)})
        except Exception as e:
            return ApiResponse(error=e)


class ModelConfigurationsAPI:
    """Model Configurations API endpoints."""
    
    def __init__(self, client: AuthenticatedClient):
        self.client = client
    
    async def list(self) -> ApiResponse[List[ModelConfigurationResponse]]:
        """List all model configurations for the organization.
        
        Returns both system defaults and organization-owned configurations.
        """
        try:
            response = await list_model_configurations_v1_model_configurations_get.asyncio(
                client=self.client,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def list_sync(self) -> ApiResponse[List[ModelConfigurationResponse]]:
        """List all model configurations for the organization (synchronous).
        
        Returns both system defaults and organization-owned configurations.
        """
        try:
            response = list_model_configurations_v1_model_configurations_get.sync(
                client=self.client,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def create(self, data: ModelConfigurationCreate) -> ApiResponse[ModelConfigurationResponse]:
        """Create a new model configuration.
        
        Args:
            data: ModelConfigurationCreate with:
                - name: Display name for the configuration
                - provider: LLM provider (openai, anthropic, google, azure, custom)
                - model_id: The model identifier (e.g., 'gpt-4o', 'claude-sonnet-4-20250514')
                - api_key: Optional API key (stored securely in Basis Theory)
                - base_url: Optional custom base URL for the provider
                - description: Optional description
        """
        try:
            response = await create_model_configuration_v1_model_configurations_post.asyncio(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def create_sync(self, data: ModelConfigurationCreate) -> ApiResponse[ModelConfigurationResponse]:
        """Create a new model configuration (synchronous)."""
        try:
            response = create_model_configuration_v1_model_configurations_post.sync(
                client=self.client,
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def get(self, model_configuration_id: str) -> ApiResponse[ModelConfigurationResponse]:
        """Get a specific model configuration by ID."""
        try:
            response = await get_model_configuration_v1_model_configurations_model_configuration_id_get.asyncio(
                client=self.client,
                model_configuration_id=_to_uuid(model_configuration_id)
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def get_sync(self, model_configuration_id: str) -> ApiResponse[ModelConfigurationResponse]:
        """Get a specific model configuration by ID (synchronous)."""
        try:
            response = get_model_configuration_v1_model_configurations_model_configuration_id_get.sync(
                client=self.client,
                model_configuration_id=_to_uuid(model_configuration_id)
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def update(self, model_configuration_id: str, data: ModelConfigurationUpdate) -> ApiResponse[ModelConfigurationResponse]:
        """Update a model configuration.
        
        Note: Only organization-owned configurations can be updated. System defaults cannot be modified.
        """
        try:
            response = await update_model_configuration_v1_model_configurations_model_configuration_id_patch.asyncio(
                client=self.client,
                model_configuration_id=_to_uuid(model_configuration_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def update_sync(self, model_configuration_id: str, data: ModelConfigurationUpdate) -> ApiResponse[ModelConfigurationResponse]:
        """Update a model configuration (synchronous)."""
        try:
            response = update_model_configuration_v1_model_configurations_model_configuration_id_patch.sync(
                client=self.client,
                model_configuration_id=_to_uuid(model_configuration_id),
                body=data
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def delete(self, model_configuration_id: str) -> ApiResponse[None]:
        """Delete a model configuration.
        
        Note: Only organization-owned configurations can be deleted. System defaults cannot be deleted.
        """
        try:
            await delete_model_configuration_v1_model_configurations_model_configuration_id_delete.asyncio(
                client=self.client,
                model_configuration_id=_to_uuid(model_configuration_id)
            )
            return ApiResponse(data=None)
        except Exception as e:
            return ApiResponse(error=e)
    
    def delete_sync(self, model_configuration_id: str) -> ApiResponse[None]:
        """Delete a model configuration (synchronous)."""
        try:
            delete_model_configuration_v1_model_configurations_model_configuration_id_delete.sync(
                client=self.client,
                model_configuration_id=_to_uuid(model_configuration_id)
            )
            return ApiResponse(data=None)
        except Exception as e:
            return ApiResponse(error=e)


class WorkflowTagGroupsAPI:
    """Workflow Tag Groups API endpoints for organizing tags."""
    
    def __init__(self, client: AuthenticatedClient):
        self.client = client
    
    async def list(self) -> ApiResponse[List[WorkflowTagGroupResponse]]:
        """
        List all workflow tag groups for your organization.
        
        Groups enable mutual exclusivity - only one tag from a group can be on a workflow.
        
        Returns:
            ApiResponse containing list of WorkflowTagGroupResponse objects
        
        Example:
            response = await client.workflow_tag_groups.list()
            for group in response.data:
                print(f"{group.emoji or ''} {group.name}")
        """
        try:
            response = await list_tag_groups_v1_workflow_tag_groups_get.asyncio(
                client=self.client
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def create(
        self,
        name: str,
        description: Optional[str] = None,
        emoji: Optional[str] = None,
        color: Optional[str] = None,
    ) -> ApiResponse[WorkflowTagGroupResponse]:
        """
        Create a new workflow tag group.
        
        Args:
            name: Group name (must be unique within organization)
            description: Optional description
            emoji: Optional emoji for the group
            color: Optional color (e.g., 'blue', 'red', 'green')
        
        Returns:
            ApiResponse containing the created WorkflowTagGroupResponse
        
        Example:
            response = await client.workflow_tag_groups.create(
                name="Priority",
                emoji="🔥",
                color="red"
            )
        """
        try:
            body = WorkflowTagGroupCreate(
                name=name,
                description=_to_unset_or_value(description),
                emoji=_to_unset_or_value(emoji),
                color=_to_unset_or_value(color),
            )
            response = await create_tag_group_v1_workflow_tag_groups_post.asyncio(
                client=self.client,
                body=body,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def get(self, group_id: Union[str, UUID]) -> ApiResponse[WorkflowTagGroupResponse]:
        """
        Get a specific workflow tag group by ID.
        
        Args:
            group_id: The group ID
        
        Returns:
            ApiResponse containing the WorkflowTagGroupResponse
        """
        try:
            response = await get_tag_group_v1_workflow_tag_groups_group_id_get.asyncio(
                client=self.client,
                group_id=str(group_id),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def update(
        self,
        group_id: Union[str, UUID],
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        emoji: Optional[str] = None,
        color: Optional[str] = None,
    ) -> ApiResponse[WorkflowTagGroupResponse]:
        """
        Update a workflow tag group.
        
        Args:
            group_id: The group ID to update
            name: New name (optional)
            description: New description (optional)
            emoji: New emoji (optional)
            color: New color (optional)
        
        Returns:
            ApiResponse containing the updated WorkflowTagGroupResponse
        """
        try:
            body = WorkflowTagGroupUpdate(
                name=_to_unset_or_value(name),
                description=_to_unset_or_value(description),
                emoji=_to_unset_or_value(emoji),
                color=_to_unset_or_value(color),
            )
            response = await update_tag_group_v1_workflow_tag_groups_group_id_patch.asyncio(
                client=self.client,
                group_id=str(group_id),
                body=body,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def delete(self, group_id: Union[str, UUID]) -> ApiResponse[None]:
        """
        Delete a workflow tag group.
        
        Tags in this group will become ungrouped (not deleted).
        
        Args:
            group_id: The group ID to delete
        
        Returns:
            ApiResponse with None on success
        """
        try:
            await delete_tag_group_v1_workflow_tag_groups_group_id_delete.asyncio(
                client=self.client,
                group_id=str(group_id),
            )
            return ApiResponse(data=None)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def reorder(self, group_ids: List[Union[str, UUID]]) -> ApiResponse[None]:
        """
        Reorder tag groups by providing IDs in desired order.
        
        Args:
            group_ids: List of group IDs in the new order
        
        Returns:
            ApiResponse with None on success
        
        Example:
            await client.workflow_tag_groups.reorder([
                "group-id-3",
                "group-id-1", 
                "group-id-2"
            ])
        """
        try:
            body = ReorderRequest(ids=[str(gid) for gid in group_ids])
            await reorder_tag_groups_v1_workflow_tag_groups_reorder_put.asyncio(
                client=self.client,
                body=body,
            )
            return ApiResponse(data=None)
        except Exception as e:
            return ApiResponse(error=e)
    
    # Synchronous methods
    def list_sync(self) -> ApiResponse[List[WorkflowTagGroupResponse]]:
        """List all workflow tag groups (synchronous)."""
        try:
            response = list_tag_groups_v1_workflow_tag_groups_get.sync(client=self.client)
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def create_sync(
        self,
        name: str,
        description: Optional[str] = None,
        emoji: Optional[str] = None,
        color: Optional[str] = None,
    ) -> ApiResponse[WorkflowTagGroupResponse]:
        """Create a new workflow tag group (synchronous)."""
        try:
            body = WorkflowTagGroupCreate(
                name=name,
                description=_to_unset_or_value(description),
                emoji=_to_unset_or_value(emoji),
                color=_to_unset_or_value(color),
            )
            response = create_tag_group_v1_workflow_tag_groups_post.sync(
                client=self.client,
                body=body,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def get_sync(self, group_id: Union[str, UUID]) -> ApiResponse[WorkflowTagGroupResponse]:
        """Get a specific workflow tag group by ID (synchronous)."""
        try:
            response = get_tag_group_v1_workflow_tag_groups_group_id_get.sync(
                client=self.client,
                group_id=str(group_id),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def update_sync(
        self,
        group_id: Union[str, UUID],
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        emoji: Optional[str] = None,
        color: Optional[str] = None,
    ) -> ApiResponse[WorkflowTagGroupResponse]:
        """Update a workflow tag group (synchronous)."""
        try:
            body = WorkflowTagGroupUpdate(
                name=_to_unset_or_value(name),
                description=_to_unset_or_value(description),
                emoji=_to_unset_or_value(emoji),
                color=_to_unset_or_value(color),
            )
            response = update_tag_group_v1_workflow_tag_groups_group_id_patch.sync(
                client=self.client,
                group_id=str(group_id),
                body=body,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def delete_sync(self, group_id: Union[str, UUID]) -> ApiResponse[None]:
        """Delete a workflow tag group (synchronous)."""
        try:
            delete_tag_group_v1_workflow_tag_groups_group_id_delete.sync(
                client=self.client,
                group_id=str(group_id),
            )
            return ApiResponse(data=None)
        except Exception as e:
            return ApiResponse(error=e)
    
    def reorder_sync(self, group_ids: List[Union[str, UUID]]) -> ApiResponse[None]:
        """Reorder tag groups by providing IDs in desired order (synchronous)."""
        try:
            body = ReorderRequest(ids=[str(gid) for gid in group_ids])
            reorder_tag_groups_v1_workflow_tag_groups_reorder_put.sync(
                client=self.client,
                body=body,
            )
            return ApiResponse(data=None)
        except Exception as e:
            return ApiResponse(error=e)


class WorkflowTagsAPI:
    """Workflow Tags API endpoints for organizing workflows."""
    
    def __init__(self, client: AuthenticatedClient):
        self.client = client
    
    async def list(
        self,
        include_archived: bool = False,
    ) -> ApiResponse[List[WorkflowTagResponse]]:
        """
        List all workflow tags for your organization.
        
        Args:
            include_archived: Whether to include archived tags (default: False)
        
        Returns:
            ApiResponse containing list of WorkflowTagResponse objects with workflow_count
        
        Example:
            response = await client.workflow_tags.list()
            for tag in response.data:
                print(f"{tag.emoji or ''} {tag.name}: {tag.workflow_count} workflows")
        """
        try:
            response = await list_tags_v1_workflow_tags_get.asyncio(
                client=self.client,
                include_archived=include_archived,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def create(
        self,
        name: str,
        description: Optional[str] = None,
        emoji: Optional[str] = None,
        color: Optional[str] = None,
        group_id: Optional[Union[str, UUID]] = None,
    ) -> ApiResponse[WorkflowTagResponse]:
        """
        Create a new workflow tag.
        
        Args:
            name: Tag name (must be unique within organization)
            description: Optional description
            emoji: Optional emoji for the tag
            color: Optional color (e.g., 'blue', 'red', 'green')
            group_id: Optional group ID for mutual exclusivity
        
        Returns:
            ApiResponse containing the created WorkflowTagResponse
        
        Example:
            # Create a standalone tag
            response = await client.workflow_tags.create(
                name="Production",
                emoji="🚀",
                color="green"
            )
            
            # Create a tag in a group (for mutual exclusivity)
            response = await client.workflow_tags.create(
                name="High Priority",
                emoji="🔴",
                group_id="priority-group-id"
            )
        """
        try:
            body = WorkflowTagCreate(
                name=name,
                description=_to_unset_or_value(description),
                emoji=_to_unset_or_value(emoji),
                color=_to_unset_or_value(color),
                group_id=_to_unset_or_value(str(group_id) if group_id else None),
            )
            response = await create_tag_v1_workflow_tags_post.asyncio(
                client=self.client,
                body=body,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def get(self, tag_id: Union[str, UUID]) -> ApiResponse[WorkflowTagResponse]:
        """
        Get a specific workflow tag by ID.
        
        Args:
            tag_id: The tag ID
        
        Returns:
            ApiResponse containing the WorkflowTagResponse
        """
        try:
            response = await get_tag_v1_workflow_tags_tag_id_get.asyncio(
                client=self.client,
                tag_id=str(tag_id),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def update(
        self,
        tag_id: Union[str, UUID],
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        emoji: Optional[str] = None,
        color: Optional[str] = None,
        group_id: Optional[Union[str, UUID]] = None,
    ) -> ApiResponse[WorkflowTagResponse]:
        """
        Update a workflow tag.
        
        Args:
            tag_id: The tag ID to update
            name: New name (optional)
            description: New description (optional)
            emoji: New emoji (optional)
            color: New color (optional)
            group_id: New group ID (optional, pass empty string to ungroup)
        
        Returns:
            ApiResponse containing the updated WorkflowTagResponse
        """
        try:
            body = WorkflowTagUpdate(
                name=_to_unset_or_value(name),
                description=_to_unset_or_value(description),
                emoji=_to_unset_or_value(emoji),
                color=_to_unset_or_value(color),
                group_id=_to_unset_or_value(str(group_id) if group_id else None),
            )
            response = await update_tag_v1_workflow_tags_tag_id_patch.asyncio(
                client=self.client,
                tag_id=str(tag_id),
                body=body,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def delete(self, tag_id: Union[str, UUID]) -> ApiResponse[None]:
        """
        Delete a workflow tag (hard delete).
        
        The tag is permanently removed and unassigned from all workflows.
        Consider using archive() instead to preserve historical data.
        
        Args:
            tag_id: The tag ID to delete
        
        Returns:
            ApiResponse with None on success
        """
        try:
            await delete_tag_v1_workflow_tags_tag_id_delete.asyncio(
                client=self.client,
                tag_id=str(tag_id),
            )
            return ApiResponse(data=None)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def archive(self, tag_id: Union[str, UUID]) -> ApiResponse[WorkflowTagResponse]:
        """
        Archive a workflow tag (soft delete).
        
        Archived tags cannot be assigned to new workflows but remain on existing ones.
        Use unarchive() to restore.
        
        Args:
            tag_id: The tag ID to archive
        
        Returns:
            ApiResponse containing the archived WorkflowTagResponse
        """
        try:
            response = await archive_tag_v1_workflow_tags_tag_id_archive_post.asyncio(
                client=self.client,
                tag_id=str(tag_id),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def unarchive(self, tag_id: Union[str, UUID]) -> ApiResponse[WorkflowTagResponse]:
        """
        Unarchive a workflow tag.
        
        Restores an archived tag so it can be assigned to workflows again.
        
        Args:
            tag_id: The tag ID to unarchive
        
        Returns:
            ApiResponse containing the unarchived WorkflowTagResponse
        """
        try:
            response = await unarchive_tag_v1_workflow_tags_tag_id_unarchive_post.asyncio(
                client=self.client,
                tag_id=str(tag_id),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def reorder(self, tag_ids: List[Union[str, UUID]]) -> ApiResponse[None]:
        """
        Reorder tags by providing IDs in desired order.
        
        Args:
            tag_ids: List of tag IDs in the new order
        
        Returns:
            ApiResponse with None on success
        
        Example:
            await client.workflow_tags.reorder([
                "tag-id-3",
                "tag-id-1", 
                "tag-id-2"
            ])
        """
        try:
            body = ReorderRequest(ids=[str(tid) for tid in tag_ids])
            await reorder_tags_v1_workflow_tags_reorder_put.asyncio(
                client=self.client,
                body=body,
            )
            return ApiResponse(data=None)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def add_to_workflow(
        self,
        workflow_id: Union[str, UUID],
        tag_ids: List[Union[str, UUID]],
    ) -> ApiResponse[List[WorkflowTagResponse]]:
        """
        Add tags to a workflow.
        
        For tags in a group (mutual exclusivity), adding a new tag from that group
        will automatically remove any existing tag from the same group.
        
        Args:
            workflow_id: The workflow ID
            tag_ids: List of tag IDs to add
        
        Returns:
            ApiResponse containing list of added WorkflowTagResponse objects
        
        Example:
            response = await client.workflow_tags.add_to_workflow(
                workflow_id="wf-123",
                tag_ids=["production-tag-id", "priority-high-tag-id"]
            )
        """
        try:
            body = AddTagsRequest(tag_ids=[str(tid) for tid in tag_ids])
            response = await add_tags_to_workflow_v1_workflows_workflow_id_tags_post.asyncio(
                client=self.client,
                workflow_id=str(workflow_id),
                body=body,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def remove_from_workflow(
        self,
        workflow_id: Union[str, UUID],
        tag_id: Union[str, UUID],
    ) -> ApiResponse[None]:
        """
        Remove a tag from a workflow.
        
        Args:
            workflow_id: The workflow ID
            tag_id: The tag ID to remove
        
        Returns:
            ApiResponse with None on success
        """
        try:
            await remove_tag_from_workflow_v1_workflows_workflow_id_tags_tag_id_delete.asyncio(
                client=self.client,
                workflow_id=str(workflow_id),
                tag_id=str(tag_id),
            )
            return ApiResponse(data=None)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def get_for_workflow(
        self,
        workflow_id: Union[str, UUID],
    ) -> ApiResponse[List[WorkflowTagResponse]]:
        """
        Get all tags assigned to a workflow.
        
        Args:
            workflow_id: The workflow ID
        
        Returns:
            ApiResponse containing list of WorkflowTagResponse objects
        """
        try:
            response = await get_workflow_tags_v1_workflows_workflow_id_tags_get.asyncio(
                client=self.client,
                workflow_id=str(workflow_id),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    async def bulk_add_to_workflows(
        self,
        workflow_ids: List[Union[str, UUID]],
        tag_ids: List[Union[str, UUID]],
    ) -> ApiResponse[None]:
        """
        Add tags to multiple workflows at once.
        
        For each workflow, mutual exclusivity is enforced.
        
        Args:
            workflow_ids: List of workflow IDs
            tag_ids: List of tag IDs to add to all workflows
        
        Returns:
            ApiResponse with None on success
        
        Example:
            await client.workflow_tags.bulk_add_to_workflows(
                workflow_ids=["wf-1", "wf-2", "wf-3"],
                tag_ids=["production-tag-id"]
            )
        """
        try:
            body = BulkAddTagsRequest(
                workflow_ids=[str(wid) for wid in workflow_ids],
                tag_ids=[str(tid) for tid in tag_ids],
            )
            await bulk_add_tags_to_workflows_v1_workflows_bulk_tags_post.asyncio(
                client=self.client,
                body=body,
            )
            return ApiResponse(data=None)
        except Exception as e:
            return ApiResponse(error=e)
    
    # Synchronous methods
    def list_sync(self, include_archived: bool = False) -> ApiResponse[List[WorkflowTagResponse]]:
        """List all workflow tags (synchronous)."""
        try:
            response = list_tags_v1_workflow_tags_get.sync(
                client=self.client,
                include_archived=include_archived,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def create_sync(
        self,
        name: str,
        description: Optional[str] = None,
        emoji: Optional[str] = None,
        color: Optional[str] = None,
        group_id: Optional[Union[str, UUID]] = None,
    ) -> ApiResponse[WorkflowTagResponse]:
        """Create a new workflow tag (synchronous)."""
        try:
            body = WorkflowTagCreate(
                name=name,
                description=_to_unset_or_value(description),
                emoji=_to_unset_or_value(emoji),
                color=_to_unset_or_value(color),
                group_id=_to_unset_or_value(str(group_id) if group_id else None),
            )
            response = create_tag_v1_workflow_tags_post.sync(
                client=self.client,
                body=body,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def get_sync(self, tag_id: Union[str, UUID]) -> ApiResponse[WorkflowTagResponse]:
        """Get a specific workflow tag by ID (synchronous)."""
        try:
            response = get_tag_v1_workflow_tags_tag_id_get.sync(
                client=self.client,
                tag_id=str(tag_id),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def update_sync(
        self,
        tag_id: Union[str, UUID],
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        emoji: Optional[str] = None,
        color: Optional[str] = None,
        group_id: Optional[Union[str, UUID]] = None,
    ) -> ApiResponse[WorkflowTagResponse]:
        """Update a workflow tag (synchronous)."""
        try:
            body = WorkflowTagUpdate(
                name=_to_unset_or_value(name),
                description=_to_unset_or_value(description),
                emoji=_to_unset_or_value(emoji),
                color=_to_unset_or_value(color),
                group_id=_to_unset_or_value(str(group_id) if group_id else None),
            )
            response = update_tag_v1_workflow_tags_tag_id_patch.sync(
                client=self.client,
                tag_id=str(tag_id),
                body=body,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def delete_sync(self, tag_id: Union[str, UUID]) -> ApiResponse[None]:
        """Delete a workflow tag (synchronous)."""
        try:
            delete_tag_v1_workflow_tags_tag_id_delete.sync(
                client=self.client,
                tag_id=str(tag_id),
            )
            return ApiResponse(data=None)
        except Exception as e:
            return ApiResponse(error=e)
    
    def archive_sync(self, tag_id: Union[str, UUID]) -> ApiResponse[WorkflowTagResponse]:
        """Archive a workflow tag (synchronous)."""
        try:
            response = archive_tag_v1_workflow_tags_tag_id_archive_post.sync(
                client=self.client,
                tag_id=str(tag_id),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def unarchive_sync(self, tag_id: Union[str, UUID]) -> ApiResponse[WorkflowTagResponse]:
        """Unarchive a workflow tag (synchronous)."""
        try:
            response = unarchive_tag_v1_workflow_tags_tag_id_unarchive_post.sync(
                client=self.client,
                tag_id=str(tag_id),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def reorder_sync(self, tag_ids: List[Union[str, UUID]]) -> ApiResponse[None]:
        """Reorder tags by providing IDs in desired order (synchronous)."""
        try:
            body = ReorderRequest(ids=[str(tid) for tid in tag_ids])
            reorder_tags_v1_workflow_tags_reorder_put.sync(
                client=self.client,
                body=body,
            )
            return ApiResponse(data=None)
        except Exception as e:
            return ApiResponse(error=e)
    
    def add_to_workflow_sync(
        self,
        workflow_id: Union[str, UUID],
        tag_ids: List[Union[str, UUID]],
    ) -> ApiResponse[List[WorkflowTagResponse]]:
        """Add tags to a workflow (synchronous)."""
        try:
            body = AddTagsRequest(tag_ids=[str(tid) for tid in tag_ids])
            response = add_tags_to_workflow_v1_workflows_workflow_id_tags_post.sync(
                client=self.client,
                workflow_id=str(workflow_id),
                body=body,
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def remove_from_workflow_sync(
        self,
        workflow_id: Union[str, UUID],
        tag_id: Union[str, UUID],
    ) -> ApiResponse[None]:
        """Remove a tag from a workflow (synchronous)."""
        try:
            remove_tag_from_workflow_v1_workflows_workflow_id_tags_tag_id_delete.sync(
                client=self.client,
                workflow_id=str(workflow_id),
                tag_id=str(tag_id),
            )
            return ApiResponse(data=None)
        except Exception as e:
            return ApiResponse(error=e)
    
    def get_for_workflow_sync(
        self,
        workflow_id: Union[str, UUID],
    ) -> ApiResponse[List[WorkflowTagResponse]]:
        """Get all tags assigned to a workflow (synchronous)."""
        try:
            response = get_workflow_tags_v1_workflows_workflow_id_tags_get.sync(
                client=self.client,
                workflow_id=str(workflow_id),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def bulk_add_to_workflows_sync(
        self,
        workflow_ids: List[Union[str, UUID]],
        tag_ids: List[Union[str, UUID]],
    ) -> ApiResponse[None]:
        """Add tags to multiple workflows at once (synchronous)."""
        try:
            body = BulkAddTagsRequest(
                workflow_ids=[str(wid) for wid in workflow_ids],
                tag_ids=[str(tid) for tid in tag_ids],
            )
            bulk_add_tags_to_workflows_v1_workflows_bulk_tags_post.sync(
                client=self.client,
                body=body,
            )
            return ApiResponse(data=None)
        except Exception as e:
            return ApiResponse(error=e)


class UsageAPI:
    """Usage API endpoints for billing and usage tracking."""
    
    def __init__(self, client: AuthenticatedClient):
        self.client = client
    
    async def aggregate(
        self,
        from_date: datetime,
        to_date: datetime,
        mode: Optional[UsageMode] = None,
    ) -> ApiResponse[UsageAggregateResponse]:
        """Aggregate usage (agentic and cached steps) for a given date range.
        
        Two modes are supported:
        - **simulated** (default): Uses total_agentic_steps and total_cached_steps from usage_metadata,
          but excludes runs where billing_outcome is 'infra_failure' (these would have been free).
          Use this for customers not yet on Stripe billing.
        - **billed**: Uses total_agentic_steps_billed and total_cached_steps_billed.
          Use this for customers on active Stripe billing.
        
        Args:
            from_date: Start of period (inclusive, datetime)
            to_date: End of period (inclusive, datetime)
            mode: Usage counting mode ('simulated' or 'billed'). Defaults to 'simulated'.
        
        Returns:
            ApiResponse with UsageAggregateResponse containing:
            - total_agentic_steps: Total agentic steps in the period
            - total_cached_steps: Total cached steps in the period
            - period_start: Start of the queried period
            - period_end: End of the queried period
            - mode: The mode used for counting
            - runs_counted: Number of runs included in the aggregation
        """
        try:
            response = await get_usage_aggregate_v1_usage_aggregate_get.asyncio(
                client=self.client,
                from_date=from_date,
                to_date=to_date,
                mode=_to_unset_or_value(mode),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)
    
    def aggregate_sync(
        self,
        from_date: datetime,
        to_date: datetime,
        mode: Optional[UsageMode] = None,
    ) -> ApiResponse[UsageAggregateResponse]:
        """Aggregate usage (agentic and cached steps) for a given date range (synchronous).
        
        Two modes are supported:
        - **simulated** (default): Uses total_agentic_steps and total_cached_steps from usage_metadata,
          but excludes runs where billing_outcome is 'infra_failure' (these would have been free).
          Use this for customers not yet on Stripe billing.
        - **billed**: Uses total_agentic_steps_billed and total_cached_steps_billed.
          Use this for customers on active Stripe billing.
        
        Args:
            from_date: Start of period (inclusive, datetime)
            to_date: End of period (inclusive, datetime)
            mode: Usage counting mode ('simulated' or 'billed'). Defaults to 'simulated'.
        
        Returns:
            ApiResponse with UsageAggregateResponse containing:
            - total_agentic_steps: Total agentic steps in the period
            - total_cached_steps: Total cached steps in the period
            - period_start: Start of the queried period
            - period_end: End of the queried period
            - mode: The mode used for counting
            - runs_counted: Number of runs included in the aggregation
        """
        try:
            response = get_usage_aggregate_v1_usage_aggregate_get.sync(
                client=self.client,
                from_date=from_date,
                to_date=to_date,
                mode=_to_unset_or_value(mode),
            )
            return ApiResponse(data=response)
        except Exception as e:
            return ApiResponse(error=e)


class CyberdeskClient:
    """Main Cyberdesk SDK client."""
    
    def __init__(
        self, 
        api_key: str, 
        base_url: str = DEFAULT_API_BASE_URL,
        timeout: Optional[httpx.Timeout] = None,
        *,
        retry: Optional[RetryConfig] = None,
        idempotency_enabled: bool = True,
        idempotency_header_name: str = "Idempotency-Key",
        idempotency_key_generator: Optional[Callable[[], str]] = None,
    ):
        """Initialize the Cyberdesk client.
        
        Args:
            api_key: Your Cyberdesk API key
            base_url: API base URL (defaults to https://api.cyberdesk.io)
            timeout: Optional httpx.Timeout configuration for request timeouts.
                    Defaults to httpx's default timeout.
            retry: Optional RetryConfig for transient failures (network/5xx/429/Retry-After).
            idempotency_enabled: If True, automatically adds Idempotency-Key to write requests
                (POST/PUT/PATCH/DELETE) so retries are safe.
            idempotency_header_name: Header name to use for idempotency.
            idempotency_key_generator: Optional callable returning a new idempotency key string.
        
        Example:
            # Basic usage
            client = CyberdeskClient('your-api-key')
            
            # With custom timeout
            client = CyberdeskClient(
                'your-api-key',
                timeout=httpx.Timeout(30.0, connect=10.0)
            )
        """
        self._base_url = base_url
        self._api_key = api_key
        self._timeout = timeout
        self._retry = retry or RetryConfig()
        self._idempotency_enabled = idempotency_enabled
        self._idempotency_header_name = idempotency_header_name
        self._idempotency_key_generator = idempotency_key_generator or (lambda: str(uuid4()))
        
        # Create the underlying client with authentication
        self._client = AuthenticatedClient(
            base_url=base_url,
            token=api_key,
            prefix="Bearer",
            auth_header_name="Authorization",
            raise_on_unexpected_status=True,  # Raise exceptions for non-200/422 responses
            timeout=timeout,
        )

        # Install retrying httpx clients so ALL generated endpoints get retries + idempotency.
        # NOTE: We set Authorization here because set_*_httpx_client overrides the generated client's defaults.
        default_headers = {"Authorization": f"Bearer {api_key}"}
        self._client.set_httpx_client(
            RetryingClient(
                base_url=base_url,
                headers=default_headers,
                timeout=timeout,
                follow_redirects=False,
                retry=self._retry,
                idempotency_enabled=self._idempotency_enabled,
                idempotency_header_name=self._idempotency_header_name,
                idempotency_key_generator=self._idempotency_key_generator,
            )
        )
        self._client.set_async_httpx_client(
            RetryingAsyncClient(
                base_url=base_url,
                headers=default_headers,
                timeout=timeout,
                follow_redirects=False,
                retry=self._retry,
                idempotency_enabled=self._idempotency_enabled,
                idempotency_header_name=self._idempotency_header_name,
                idempotency_key_generator=self._idempotency_key_generator,
            )
        )
        
        # Initialize API endpoints
        self.machines = MachinesAPI(self._client)
        self.pools = PoolsAPI(self._client)
        self.workflows = WorkflowsAPI(self._client)
        self.workflow_tags = WorkflowTagsAPI(self._client)
        self.workflow_tag_groups = WorkflowTagGroupsAPI(self._client)
        self.runs = RunsAPI(self._client)
        self.connections = ConnectionsAPI(self._client)
        self.trajectories = TrajectoriesAPI(self._client)
        self.run_attachments = RunAttachmentsAPI(self._client)
        self.model_configurations = ModelConfigurationsAPI(self._client)
        self.usage = UsageAPI(self._client)
        
        # TODO: Add computer API for screenshot functionality
        # The openapi-python-client doesn't generate code for binary responses like PNG images
        # To add screenshot support, implement a ComputerAPI class that:
        # - Makes raw HTTP GET request to /v1/computer/{machine_id}/display/screenshot
        # - Returns the PNG image bytes
        # Example: self.computer = ComputerAPI(self._client)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def close(self):
        """Close the client connection."""
        if hasattr(self._client, '__exit__'):
            self._client.__exit__(None, None, None) 
from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.machine_status import MachineStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.included_resource import IncludedResource
    from ..models.machine_response_with_includes_machine_parameters_type_0 import (
        MachineResponseWithIncludesMachineParametersType0,
    )
    from ..models.machine_response_with_includes_machine_sensitive_parameters_type_0 import (
        MachineResponseWithIncludesMachineSensitiveParametersType0,
    )
    from ..models.pool_response import PoolResponse


T = TypeVar("T", bound="MachineResponseWithIncludes")


@_attrs_define
class MachineResponseWithIncludes:
    """Machine response with optional included related resources.

    Attributes:
        id (UUID):
        fingerprint (str):
        unkey_key_id (str):
        status (MachineStatus):
        is_available (bool):
        created_at (datetime.datetime):
        last_seen (datetime.datetime):
        user_id (None | Unset | UUID):
        organization_id (None | str | Unset):
        name (None | str | Unset):
        version (None | str | Unset):
        hostname (None | str | Unset):
        os_info (None | str | Unset):
        machine_parameters (MachineResponseWithIncludesMachineParametersType0 | None | Unset):
        machine_sensitive_parameters (MachineResponseWithIncludesMachineSensitiveParametersType0 | None | Unset):
        reserved_session_id (None | Unset | UUID):
        linked_keepalive_machine_id (None | Unset | UUID):
        physical_server_id (None | str | Unset):
        pools (list[PoolResponse] | None | Unset):
        included (list[IncludedResource] | None | Unset): Related resources requested via the `include` query parameter
    """

    id: UUID
    fingerprint: str
    unkey_key_id: str
    status: MachineStatus
    is_available: bool
    created_at: datetime.datetime
    last_seen: datetime.datetime
    user_id: None | Unset | UUID = UNSET
    organization_id: None | str | Unset = UNSET
    name: None | str | Unset = UNSET
    version: None | str | Unset = UNSET
    hostname: None | str | Unset = UNSET
    os_info: None | str | Unset = UNSET
    machine_parameters: MachineResponseWithIncludesMachineParametersType0 | None | Unset = UNSET
    machine_sensitive_parameters: MachineResponseWithIncludesMachineSensitiveParametersType0 | None | Unset = UNSET
    reserved_session_id: None | Unset | UUID = UNSET
    linked_keepalive_machine_id: None | Unset | UUID = UNSET
    physical_server_id: None | str | Unset = UNSET
    pools: list[PoolResponse] | None | Unset = UNSET
    included: list[IncludedResource] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.machine_response_with_includes_machine_parameters_type_0 import (
            MachineResponseWithIncludesMachineParametersType0,
        )
        from ..models.machine_response_with_includes_machine_sensitive_parameters_type_0 import (
            MachineResponseWithIncludesMachineSensitiveParametersType0,
        )

        id = str(self.id)

        fingerprint = self.fingerprint

        unkey_key_id = self.unkey_key_id

        status = self.status.value

        is_available = self.is_available

        created_at = self.created_at.isoformat()

        last_seen = self.last_seen.isoformat()

        user_id: None | str | Unset
        if isinstance(self.user_id, Unset):
            user_id = UNSET
        elif isinstance(self.user_id, UUID):
            user_id = str(self.user_id)
        else:
            user_id = self.user_id

        organization_id: None | str | Unset
        if isinstance(self.organization_id, Unset):
            organization_id = UNSET
        else:
            organization_id = self.organization_id

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        version: None | str | Unset
        if isinstance(self.version, Unset):
            version = UNSET
        else:
            version = self.version

        hostname: None | str | Unset
        if isinstance(self.hostname, Unset):
            hostname = UNSET
        else:
            hostname = self.hostname

        os_info: None | str | Unset
        if isinstance(self.os_info, Unset):
            os_info = UNSET
        else:
            os_info = self.os_info

        machine_parameters: dict[str, Any] | None | Unset
        if isinstance(self.machine_parameters, Unset):
            machine_parameters = UNSET
        elif isinstance(self.machine_parameters, MachineResponseWithIncludesMachineParametersType0):
            machine_parameters = self.machine_parameters.to_dict()
        else:
            machine_parameters = self.machine_parameters

        machine_sensitive_parameters: dict[str, Any] | None | Unset
        if isinstance(self.machine_sensitive_parameters, Unset):
            machine_sensitive_parameters = UNSET
        elif isinstance(self.machine_sensitive_parameters, MachineResponseWithIncludesMachineSensitiveParametersType0):
            machine_sensitive_parameters = self.machine_sensitive_parameters.to_dict()
        else:
            machine_sensitive_parameters = self.machine_sensitive_parameters

        reserved_session_id: None | str | Unset
        if isinstance(self.reserved_session_id, Unset):
            reserved_session_id = UNSET
        elif isinstance(self.reserved_session_id, UUID):
            reserved_session_id = str(self.reserved_session_id)
        else:
            reserved_session_id = self.reserved_session_id

        linked_keepalive_machine_id: None | str | Unset
        if isinstance(self.linked_keepalive_machine_id, Unset):
            linked_keepalive_machine_id = UNSET
        elif isinstance(self.linked_keepalive_machine_id, UUID):
            linked_keepalive_machine_id = str(self.linked_keepalive_machine_id)
        else:
            linked_keepalive_machine_id = self.linked_keepalive_machine_id

        physical_server_id: None | str | Unset
        if isinstance(self.physical_server_id, Unset):
            physical_server_id = UNSET
        else:
            physical_server_id = self.physical_server_id

        pools: list[dict[str, Any]] | None | Unset
        if isinstance(self.pools, Unset):
            pools = UNSET
        elif isinstance(self.pools, list):
            pools = []
            for pools_type_0_item_data in self.pools:
                pools_type_0_item = pools_type_0_item_data.to_dict()
                pools.append(pools_type_0_item)

        else:
            pools = self.pools

        included: list[dict[str, Any]] | None | Unset
        if isinstance(self.included, Unset):
            included = UNSET
        elif isinstance(self.included, list):
            included = []
            for included_type_0_item_data in self.included:
                included_type_0_item = included_type_0_item_data.to_dict()
                included.append(included_type_0_item)

        else:
            included = self.included

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "fingerprint": fingerprint,
                "unkey_key_id": unkey_key_id,
                "status": status,
                "is_available": is_available,
                "created_at": created_at,
                "last_seen": last_seen,
            }
        )
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if organization_id is not UNSET:
            field_dict["organization_id"] = organization_id
        if name is not UNSET:
            field_dict["name"] = name
        if version is not UNSET:
            field_dict["version"] = version
        if hostname is not UNSET:
            field_dict["hostname"] = hostname
        if os_info is not UNSET:
            field_dict["os_info"] = os_info
        if machine_parameters is not UNSET:
            field_dict["machine_parameters"] = machine_parameters
        if machine_sensitive_parameters is not UNSET:
            field_dict["machine_sensitive_parameters"] = machine_sensitive_parameters
        if reserved_session_id is not UNSET:
            field_dict["reserved_session_id"] = reserved_session_id
        if linked_keepalive_machine_id is not UNSET:
            field_dict["linked_keepalive_machine_id"] = linked_keepalive_machine_id
        if physical_server_id is not UNSET:
            field_dict["physical_server_id"] = physical_server_id
        if pools is not UNSET:
            field_dict["pools"] = pools
        if included is not UNSET:
            field_dict["included"] = included

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.included_resource import IncludedResource
        from ..models.machine_response_with_includes_machine_parameters_type_0 import (
            MachineResponseWithIncludesMachineParametersType0,
        )
        from ..models.machine_response_with_includes_machine_sensitive_parameters_type_0 import (
            MachineResponseWithIncludesMachineSensitiveParametersType0,
        )
        from ..models.pool_response import PoolResponse

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        fingerprint = d.pop("fingerprint")

        unkey_key_id = d.pop("unkey_key_id")

        status = MachineStatus(d.pop("status"))

        is_available = d.pop("is_available")

        created_at = isoparse(d.pop("created_at"))

        last_seen = isoparse(d.pop("last_seen"))

        def _parse_user_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                user_id_type_0 = UUID(data)

                return user_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        user_id = _parse_user_id(d.pop("user_id", UNSET))

        def _parse_organization_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        organization_id = _parse_organization_id(d.pop("organization_id", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_version(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        version = _parse_version(d.pop("version", UNSET))

        def _parse_hostname(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        hostname = _parse_hostname(d.pop("hostname", UNSET))

        def _parse_os_info(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        os_info = _parse_os_info(d.pop("os_info", UNSET))

        def _parse_machine_parameters(data: object) -> MachineResponseWithIncludesMachineParametersType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                machine_parameters_type_0 = MachineResponseWithIncludesMachineParametersType0.from_dict(data)

                return machine_parameters_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MachineResponseWithIncludesMachineParametersType0 | None | Unset, data)

        machine_parameters = _parse_machine_parameters(d.pop("machine_parameters", UNSET))

        def _parse_machine_sensitive_parameters(
            data: object,
        ) -> MachineResponseWithIncludesMachineSensitiveParametersType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                machine_sensitive_parameters_type_0 = (
                    MachineResponseWithIncludesMachineSensitiveParametersType0.from_dict(data)
                )

                return machine_sensitive_parameters_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MachineResponseWithIncludesMachineSensitiveParametersType0 | None | Unset, data)

        machine_sensitive_parameters = _parse_machine_sensitive_parameters(d.pop("machine_sensitive_parameters", UNSET))

        def _parse_reserved_session_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                reserved_session_id_type_0 = UUID(data)

                return reserved_session_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        reserved_session_id = _parse_reserved_session_id(d.pop("reserved_session_id", UNSET))

        def _parse_linked_keepalive_machine_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                linked_keepalive_machine_id_type_0 = UUID(data)

                return linked_keepalive_machine_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        linked_keepalive_machine_id = _parse_linked_keepalive_machine_id(d.pop("linked_keepalive_machine_id", UNSET))

        def _parse_physical_server_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        physical_server_id = _parse_physical_server_id(d.pop("physical_server_id", UNSET))

        def _parse_pools(data: object) -> list[PoolResponse] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                pools_type_0 = []
                _pools_type_0 = data
                for pools_type_0_item_data in _pools_type_0:
                    pools_type_0_item = PoolResponse.from_dict(pools_type_0_item_data)

                    pools_type_0.append(pools_type_0_item)

                return pools_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[PoolResponse] | None | Unset, data)

        pools = _parse_pools(d.pop("pools", UNSET))

        def _parse_included(data: object) -> list[IncludedResource] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                included_type_0 = []
                _included_type_0 = data
                for included_type_0_item_data in _included_type_0:
                    included_type_0_item = IncludedResource.from_dict(included_type_0_item_data)

                    included_type_0.append(included_type_0_item)

                return included_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[IncludedResource] | None | Unset, data)

        included = _parse_included(d.pop("included", UNSET))

        machine_response_with_includes = cls(
            id=id,
            fingerprint=fingerprint,
            unkey_key_id=unkey_key_id,
            status=status,
            is_available=is_available,
            created_at=created_at,
            last_seen=last_seen,
            user_id=user_id,
            organization_id=organization_id,
            name=name,
            version=version,
            hostname=hostname,
            os_info=os_info,
            machine_parameters=machine_parameters,
            machine_sensitive_parameters=machine_sensitive_parameters,
            reserved_session_id=reserved_session_id,
            linked_keepalive_machine_id=linked_keepalive_machine_id,
            physical_server_id=physical_server_id,
            pools=pools,
            included=included,
        )

        machine_response_with_includes.additional_properties = d
        return machine_response_with_includes

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties

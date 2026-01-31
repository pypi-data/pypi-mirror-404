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
    from ..models.machine_update_machine_parameters_type_0 import MachineUpdateMachineParametersType0
    from ..models.machine_update_machine_sensitive_parameters_type_0 import MachineUpdateMachineSensitiveParametersType0


T = TypeVar("T", bound="MachineUpdate")


@_attrs_define
class MachineUpdate:
    """Schema for updating a machine

    Attributes:
        name (None | str | Unset):
        version (None | str | Unset):
        hostname (None | str | Unset):
        os_info (None | str | Unset):
        status (MachineStatus | None | Unset):
        is_available (bool | None | Unset):
        last_seen (datetime.datetime | None | Unset):
        reserved_session_id (None | Unset | UUID): Set to null to clear reservation; server will cancel any
            scheduling/running run on this machine, clear reservation, mark machine available, and trigger matching
        machine_parameters (MachineUpdateMachineParametersType0 | None | Unset): Machine-specific input values. Provide
            empty dict {} to clear all.
        machine_sensitive_parameters (MachineUpdateMachineSensitiveParametersType0 | None | Unset): Machine-specific
            sensitive input values (will be stored in Basis Theory). Provide empty dict {} to clear all.
    """

    name: None | str | Unset = UNSET
    version: None | str | Unset = UNSET
    hostname: None | str | Unset = UNSET
    os_info: None | str | Unset = UNSET
    status: MachineStatus | None | Unset = UNSET
    is_available: bool | None | Unset = UNSET
    last_seen: datetime.datetime | None | Unset = UNSET
    reserved_session_id: None | Unset | UUID = UNSET
    machine_parameters: MachineUpdateMachineParametersType0 | None | Unset = UNSET
    machine_sensitive_parameters: MachineUpdateMachineSensitiveParametersType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.machine_update_machine_parameters_type_0 import MachineUpdateMachineParametersType0
        from ..models.machine_update_machine_sensitive_parameters_type_0 import (
            MachineUpdateMachineSensitiveParametersType0,
        )

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

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, MachineStatus):
            status = self.status.value
        else:
            status = self.status

        is_available: bool | None | Unset
        if isinstance(self.is_available, Unset):
            is_available = UNSET
        else:
            is_available = self.is_available

        last_seen: None | str | Unset
        if isinstance(self.last_seen, Unset):
            last_seen = UNSET
        elif isinstance(self.last_seen, datetime.datetime):
            last_seen = self.last_seen.isoformat()
        else:
            last_seen = self.last_seen

        reserved_session_id: None | str | Unset
        if isinstance(self.reserved_session_id, Unset):
            reserved_session_id = UNSET
        elif isinstance(self.reserved_session_id, UUID):
            reserved_session_id = str(self.reserved_session_id)
        else:
            reserved_session_id = self.reserved_session_id

        machine_parameters: dict[str, Any] | None | Unset
        if isinstance(self.machine_parameters, Unset):
            machine_parameters = UNSET
        elif isinstance(self.machine_parameters, MachineUpdateMachineParametersType0):
            machine_parameters = self.machine_parameters.to_dict()
        else:
            machine_parameters = self.machine_parameters

        machine_sensitive_parameters: dict[str, Any] | None | Unset
        if isinstance(self.machine_sensitive_parameters, Unset):
            machine_sensitive_parameters = UNSET
        elif isinstance(self.machine_sensitive_parameters, MachineUpdateMachineSensitiveParametersType0):
            machine_sensitive_parameters = self.machine_sensitive_parameters.to_dict()
        else:
            machine_sensitive_parameters = self.machine_sensitive_parameters

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if version is not UNSET:
            field_dict["version"] = version
        if hostname is not UNSET:
            field_dict["hostname"] = hostname
        if os_info is not UNSET:
            field_dict["os_info"] = os_info
        if status is not UNSET:
            field_dict["status"] = status
        if is_available is not UNSET:
            field_dict["is_available"] = is_available
        if last_seen is not UNSET:
            field_dict["last_seen"] = last_seen
        if reserved_session_id is not UNSET:
            field_dict["reserved_session_id"] = reserved_session_id
        if machine_parameters is not UNSET:
            field_dict["machine_parameters"] = machine_parameters
        if machine_sensitive_parameters is not UNSET:
            field_dict["machine_sensitive_parameters"] = machine_sensitive_parameters

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.machine_update_machine_parameters_type_0 import MachineUpdateMachineParametersType0
        from ..models.machine_update_machine_sensitive_parameters_type_0 import (
            MachineUpdateMachineSensitiveParametersType0,
        )

        d = dict(src_dict)

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

        def _parse_status(data: object) -> MachineStatus | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                status_type_0 = MachineStatus(data)

                return status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MachineStatus | None | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_is_available(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_available = _parse_is_available(d.pop("is_available", UNSET))

        def _parse_last_seen(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_seen_type_0 = isoparse(data)

                return last_seen_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_seen = _parse_last_seen(d.pop("last_seen", UNSET))

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

        def _parse_machine_parameters(data: object) -> MachineUpdateMachineParametersType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                machine_parameters_type_0 = MachineUpdateMachineParametersType0.from_dict(data)

                return machine_parameters_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MachineUpdateMachineParametersType0 | None | Unset, data)

        machine_parameters = _parse_machine_parameters(d.pop("machine_parameters", UNSET))

        def _parse_machine_sensitive_parameters(
            data: object,
        ) -> MachineUpdateMachineSensitiveParametersType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                machine_sensitive_parameters_type_0 = MachineUpdateMachineSensitiveParametersType0.from_dict(data)

                return machine_sensitive_parameters_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MachineUpdateMachineSensitiveParametersType0 | None | Unset, data)

        machine_sensitive_parameters = _parse_machine_sensitive_parameters(d.pop("machine_sensitive_parameters", UNSET))

        machine_update = cls(
            name=name,
            version=version,
            hostname=hostname,
            os_info=os_info,
            status=status,
            is_available=is_available,
            last_seen=last_seen,
            reserved_session_id=reserved_session_id,
            machine_parameters=machine_parameters,
            machine_sensitive_parameters=machine_sensitive_parameters,
        )

        machine_update.additional_properties = d
        return machine_update

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

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.machine_create_machine_parameters_type_0 import MachineCreateMachineParametersType0
    from ..models.machine_create_machine_sensitive_parameters_type_0 import MachineCreateMachineSensitiveParametersType0


T = TypeVar("T", bound="MachineCreate")


@_attrs_define
class MachineCreate:
    """Schema for creating a machine

    Attributes:
        fingerprint (str):
        unkey_key_id (str):
        name (None | str | Unset):
        version (None | str | Unset):
        hostname (None | str | Unset):
        os_info (None | str | Unset):
        machine_parameters (MachineCreateMachineParametersType0 | None | Unset): Machine-specific input values that
            auto-populate runs
        machine_sensitive_parameters (MachineCreateMachineSensitiveParametersType0 | None | Unset): Machine-specific
            sensitive input aliases (stored in Basis Theory)
    """

    fingerprint: str
    unkey_key_id: str
    name: None | str | Unset = UNSET
    version: None | str | Unset = UNSET
    hostname: None | str | Unset = UNSET
    os_info: None | str | Unset = UNSET
    machine_parameters: MachineCreateMachineParametersType0 | None | Unset = UNSET
    machine_sensitive_parameters: MachineCreateMachineSensitiveParametersType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.machine_create_machine_parameters_type_0 import MachineCreateMachineParametersType0
        from ..models.machine_create_machine_sensitive_parameters_type_0 import (
            MachineCreateMachineSensitiveParametersType0,
        )

        fingerprint = self.fingerprint

        unkey_key_id = self.unkey_key_id

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
        elif isinstance(self.machine_parameters, MachineCreateMachineParametersType0):
            machine_parameters = self.machine_parameters.to_dict()
        else:
            machine_parameters = self.machine_parameters

        machine_sensitive_parameters: dict[str, Any] | None | Unset
        if isinstance(self.machine_sensitive_parameters, Unset):
            machine_sensitive_parameters = UNSET
        elif isinstance(self.machine_sensitive_parameters, MachineCreateMachineSensitiveParametersType0):
            machine_sensitive_parameters = self.machine_sensitive_parameters.to_dict()
        else:
            machine_sensitive_parameters = self.machine_sensitive_parameters

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "fingerprint": fingerprint,
                "unkey_key_id": unkey_key_id,
            }
        )
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.machine_create_machine_parameters_type_0 import MachineCreateMachineParametersType0
        from ..models.machine_create_machine_sensitive_parameters_type_0 import (
            MachineCreateMachineSensitiveParametersType0,
        )

        d = dict(src_dict)
        fingerprint = d.pop("fingerprint")

        unkey_key_id = d.pop("unkey_key_id")

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

        def _parse_machine_parameters(data: object) -> MachineCreateMachineParametersType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                machine_parameters_type_0 = MachineCreateMachineParametersType0.from_dict(data)

                return machine_parameters_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MachineCreateMachineParametersType0 | None | Unset, data)

        machine_parameters = _parse_machine_parameters(d.pop("machine_parameters", UNSET))

        def _parse_machine_sensitive_parameters(
            data: object,
        ) -> MachineCreateMachineSensitiveParametersType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                machine_sensitive_parameters_type_0 = MachineCreateMachineSensitiveParametersType0.from_dict(data)

                return machine_sensitive_parameters_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MachineCreateMachineSensitiveParametersType0 | None | Unset, data)

        machine_sensitive_parameters = _parse_machine_sensitive_parameters(d.pop("machine_sensitive_parameters", UNSET))

        machine_create = cls(
            fingerprint=fingerprint,
            unkey_key_id=unkey_key_id,
            name=name,
            version=version,
            hostname=hostname,
            os_info=os_info,
            machine_parameters=machine_parameters,
            machine_sensitive_parameters=machine_sensitive_parameters,
        )

        machine_create.additional_properties = d
        return machine_create

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

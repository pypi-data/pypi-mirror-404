from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.included_resource import IncludedResource
    from ..models.machine_response import MachineResponse


T = TypeVar("T", bound="PoolResponseWithIncludes")


@_attrs_define
class PoolResponseWithIncludes:
    """Pool response with optional included related resources.

    Attributes:
        id (UUID):
        organization_id (str):
        name (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        description (None | str | Unset):
        machine_count (int | None | Unset): Number of machines in this pool Default: 0.
        machines (list[MachineResponse] | None | Unset): [Deprecated] Machines in this pool. Use `included` array
            instead.
        included (list[IncludedResource] | None | Unset): Related resources requested via the `include` query parameter
    """

    id: UUID
    organization_id: str
    name: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    description: None | str | Unset = UNSET
    machine_count: int | None | Unset = 0
    machines: list[MachineResponse] | None | Unset = UNSET
    included: list[IncludedResource] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        organization_id = self.organization_id

        name = self.name

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        machine_count: int | None | Unset
        if isinstance(self.machine_count, Unset):
            machine_count = UNSET
        else:
            machine_count = self.machine_count

        machines: list[dict[str, Any]] | None | Unset
        if isinstance(self.machines, Unset):
            machines = UNSET
        elif isinstance(self.machines, list):
            machines = []
            for machines_type_0_item_data in self.machines:
                machines_type_0_item = machines_type_0_item_data.to_dict()
                machines.append(machines_type_0_item)

        else:
            machines = self.machines

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
                "organization_id": organization_id,
                "name": name,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if machine_count is not UNSET:
            field_dict["machine_count"] = machine_count
        if machines is not UNSET:
            field_dict["machines"] = machines
        if included is not UNSET:
            field_dict["included"] = included

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.included_resource import IncludedResource
        from ..models.machine_response import MachineResponse

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        organization_id = d.pop("organization_id")

        name = d.pop("name")

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_machine_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        machine_count = _parse_machine_count(d.pop("machine_count", UNSET))

        def _parse_machines(data: object) -> list[MachineResponse] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                machines_type_0 = []
                _machines_type_0 = data
                for machines_type_0_item_data in _machines_type_0:
                    machines_type_0_item = MachineResponse.from_dict(machines_type_0_item_data)

                    machines_type_0.append(machines_type_0_item)

                return machines_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[MachineResponse] | None | Unset, data)

        machines = _parse_machines(d.pop("machines", UNSET))

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

        pool_response_with_includes = cls(
            id=id,
            organization_id=organization_id,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            description=description,
            machine_count=machine_count,
            machines=machines,
            included=included,
        )

        pool_response_with_includes.additional_properties = d
        return pool_response_with_includes

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

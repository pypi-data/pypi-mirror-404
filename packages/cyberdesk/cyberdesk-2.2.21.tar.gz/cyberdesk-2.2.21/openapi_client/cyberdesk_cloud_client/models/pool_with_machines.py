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
    from ..models.machine_response import MachineResponse


T = TypeVar("T", bound="PoolWithMachines")


@_attrs_define
class PoolWithMachines:
    """Pool response with machines included

    Attributes:
        name (str):
        id (UUID):
        organization_id (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        description (None | str | Unset):
        machine_count (int | None | Unset): Number of machines in this pool Default: 0.
        machines (list[MachineResponse] | Unset):
    """

    name: str
    id: UUID
    organization_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    description: None | str | Unset = UNSET
    machine_count: int | None | Unset = 0
    machines: list[MachineResponse] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        id = str(self.id)

        organization_id = self.organization_id

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

        machines: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.machines, Unset):
            machines = []
            for machines_item_data in self.machines:
                machines_item = machines_item_data.to_dict()
                machines.append(machines_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "id": id,
                "organization_id": organization_id,
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.machine_response import MachineResponse

        d = dict(src_dict)
        name = d.pop("name")

        id = UUID(d.pop("id"))

        organization_id = d.pop("organization_id")

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

        _machines = d.pop("machines", UNSET)
        machines: list[MachineResponse] | Unset = UNSET
        if _machines is not UNSET:
            machines = []
            for machines_item_data in _machines:
                machines_item = MachineResponse.from_dict(machines_item_data)

                machines.append(machines_item)

        pool_with_machines = cls(
            name=name,
            id=id,
            organization_id=organization_id,
            created_at=created_at,
            updated_at=updated_at,
            description=description,
            machine_count=machine_count,
            machines=machines,
        )

        pool_with_machines.additional_properties = d
        return pool_with_machines

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

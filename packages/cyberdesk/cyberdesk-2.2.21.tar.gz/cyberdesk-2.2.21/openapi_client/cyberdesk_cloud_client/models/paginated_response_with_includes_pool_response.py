from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.included_resource import IncludedResource
    from ..models.pool_response import PoolResponse


T = TypeVar("T", bound="PaginatedResponseWithIncludesPoolResponse")


@_attrs_define
class PaginatedResponseWithIncludesPoolResponse:
    """
    Attributes:
        items (list[PoolResponse]):
        total (int):
        skip (int):
        limit (int):
        included (list[IncludedResource] | None | Unset): Related resources requested via the `include` query parameter
    """

    items: list[PoolResponse]
    total: int
    skip: int
    limit: int
    included: list[IncludedResource] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        total = self.total

        skip = self.skip

        limit = self.limit

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
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        )
        if included is not UNSET:
            field_dict["included"] = included

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.included_resource import IncludedResource
        from ..models.pool_response import PoolResponse

        d = dict(src_dict)
        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = PoolResponse.from_dict(items_item_data)

            items.append(items_item)

        total = d.pop("total")

        skip = d.pop("skip")

        limit = d.pop("limit")

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

        paginated_response_with_includes_pool_response = cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            included=included,
        )

        paginated_response_with_includes_pool_response.additional_properties = d
        return paginated_response_with_includes_pool_response

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

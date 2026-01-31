from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.filter_expression_model import FilterExpressionModel
    from ..models.pagination_filter import PaginationFilter
    from ..models.sort_expression_model import SortExpressionModel


T = TypeVar("T", bound="InventoryBrowserFilters")


@_attrs_define
class InventoryBrowserFilters:
    """
    Attributes:
        pagination (PaginationFilter | Unset): Pagination settings.
        filter_ (FilterExpressionModel | Unset): Filter settings.
        sorting (SortExpressionModel | Unset): Sorting settings.
        hierarchy_type (str | Unset): Hierarchy type. The possible values you can specify depend on the used request.
            <p> <ul> <li>For the [Get All Servers](Inventory-Browser#operation/GetAllInventoryHosts) and [Get Inventory
            Objects](Inventory-Browser#operation/GetInventoryObjects) requests, specify values depending on the
            virtualization platform&#58; <ul> <li> For VMware vSphere&#58; *HostsAndClusters*, *DatastoresAndVms*,
            *HostsAndDatastores*, *VmsAndTemplates*, *VmsAndTags*, *Network* </li> <li> For VMware Cloud Director&#58;
            *VAppsAndVms*, *Network*, *StoragePolicies*, *Datastores* </li> <li> For Microsoft Hyper-V&#58; *HostsAndVMs*,
            *Hosts*, *HostsAndVolumes*, *VMGroups*, *Tags*, *Network* </li> </ul> </li> <li> For the [Get All Protection
            Groups](Inventory-Browser#operation/GetAllInventoryPGs) and [Get Inventory Objects for Specific Protection
            Group](Inventory-Browser#operation/GetInventoryForPG) requests, use the following values&#58; *Computers*,
            *Clusters* </li> </ul>
    """

    pagination: PaginationFilter | Unset = UNSET
    filter_: FilterExpressionModel | Unset = UNSET
    sorting: SortExpressionModel | Unset = UNSET
    hierarchy_type: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        pagination: dict[str, Any] | Unset = UNSET
        if not isinstance(self.pagination, Unset):
            pagination = self.pagination.to_dict()

        filter_: dict[str, Any] | Unset = UNSET
        if not isinstance(self.filter_, Unset):
            filter_ = self.filter_.to_dict()

        sorting: dict[str, Any] | Unset = UNSET
        if not isinstance(self.sorting, Unset):
            sorting = self.sorting.to_dict()

        hierarchy_type = self.hierarchy_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if pagination is not UNSET:
            field_dict["pagination"] = pagination
        if filter_ is not UNSET:
            field_dict["filter"] = filter_
        if sorting is not UNSET:
            field_dict["sorting"] = sorting
        if hierarchy_type is not UNSET:
            field_dict["hierarchyType"] = hierarchy_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.filter_expression_model import FilterExpressionModel
        from ..models.pagination_filter import PaginationFilter
        from ..models.sort_expression_model import SortExpressionModel

        d = dict(src_dict)
        _pagination = d.pop("pagination", UNSET)
        pagination: PaginationFilter | Unset
        if isinstance(_pagination, Unset):
            pagination = UNSET
        else:
            pagination = PaginationFilter.from_dict(_pagination)

        _filter_ = d.pop("filter", UNSET)
        filter_: FilterExpressionModel | Unset
        if isinstance(_filter_, Unset):
            filter_ = UNSET
        else:
            filter_ = FilterExpressionModel.from_dict(_filter_)

        _sorting = d.pop("sorting", UNSET)
        sorting: SortExpressionModel | Unset
        if isinstance(_sorting, Unset):
            sorting = UNSET
        else:
            sorting = SortExpressionModel.from_dict(_sorting)

        hierarchy_type = d.pop("hierarchyType", UNSET)

        inventory_browser_filters = cls(
            pagination=pagination,
            filter_=filter_,
            sorting=sorting,
            hierarchy_type=hierarchy_type,
        )

        inventory_browser_filters.additional_properties = d
        return inventory_browser_filters

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

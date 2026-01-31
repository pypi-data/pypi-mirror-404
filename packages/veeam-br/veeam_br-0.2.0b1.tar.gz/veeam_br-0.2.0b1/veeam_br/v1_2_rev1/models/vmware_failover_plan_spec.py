from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_failover_plan_type import EFailoverPlanType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.failover_plan_script_model import FailoverPlanScriptModel
    from ..models.vmware_failover_plan_virtual_machine_model import VmwareFailoverPlanVirtualMachineModel


T = TypeVar("T", bound="VmwareFailoverPlanSpec")


@_attrs_define
class VmwareFailoverPlanSpec:
    """
    Attributes:
        type_ (EFailoverPlanType): Type of failover plan.
        name (str | Unset):
        description (str | Unset):
        pre_failover_script (FailoverPlanScriptModel | Unset):
        post_failover_script (FailoverPlanScriptModel | Unset):
        virtual_machines (list[VmwareFailoverPlanVirtualMachineModel] | Unset):
    """

    type_: EFailoverPlanType
    name: str | Unset = UNSET
    description: str | Unset = UNSET
    pre_failover_script: FailoverPlanScriptModel | Unset = UNSET
    post_failover_script: FailoverPlanScriptModel | Unset = UNSET
    virtual_machines: list[VmwareFailoverPlanVirtualMachineModel] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        name = self.name

        description = self.description

        pre_failover_script: dict[str, Any] | Unset = UNSET
        if not isinstance(self.pre_failover_script, Unset):
            pre_failover_script = self.pre_failover_script.to_dict()

        post_failover_script: dict[str, Any] | Unset = UNSET
        if not isinstance(self.post_failover_script, Unset):
            post_failover_script = self.post_failover_script.to_dict()

        virtual_machines: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.virtual_machines, Unset):
            virtual_machines = []
            for virtual_machines_item_data in self.virtual_machines:
                virtual_machines_item = virtual_machines_item_data.to_dict()
                virtual_machines.append(virtual_machines_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if pre_failover_script is not UNSET:
            field_dict["preFailoverScript"] = pre_failover_script
        if post_failover_script is not UNSET:
            field_dict["postFailoverScript"] = post_failover_script
        if virtual_machines is not UNSET:
            field_dict["virtualMachines"] = virtual_machines

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.failover_plan_script_model import FailoverPlanScriptModel
        from ..models.vmware_failover_plan_virtual_machine_model import VmwareFailoverPlanVirtualMachineModel

        d = dict(src_dict)
        type_ = EFailoverPlanType(d.pop("type"))

        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        _pre_failover_script = d.pop("preFailoverScript", UNSET)
        pre_failover_script: FailoverPlanScriptModel | Unset
        if isinstance(_pre_failover_script, Unset):
            pre_failover_script = UNSET
        else:
            pre_failover_script = FailoverPlanScriptModel.from_dict(_pre_failover_script)

        _post_failover_script = d.pop("postFailoverScript", UNSET)
        post_failover_script: FailoverPlanScriptModel | Unset
        if isinstance(_post_failover_script, Unset):
            post_failover_script = UNSET
        else:
            post_failover_script = FailoverPlanScriptModel.from_dict(_post_failover_script)

        _virtual_machines = d.pop("virtualMachines", UNSET)
        virtual_machines: list[VmwareFailoverPlanVirtualMachineModel] | Unset = UNSET
        if _virtual_machines is not UNSET:
            virtual_machines = []
            for virtual_machines_item_data in _virtual_machines:
                virtual_machines_item = VmwareFailoverPlanVirtualMachineModel.from_dict(virtual_machines_item_data)

                virtual_machines.append(virtual_machines_item)

        vmware_failover_plan_spec = cls(
            type_=type_,
            name=name,
            description=description,
            pre_failover_script=pre_failover_script,
            post_failover_script=post_failover_script,
            virtual_machines=virtual_machines,
        )

        vmware_failover_plan_spec.additional_properties = d
        return vmware_failover_plan_spec

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

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.ad_object_model import ADObjectModel


T = TypeVar("T", bound="ADObjectCustomCredentialsModel")


@_attrs_define
class ADObjectCustomCredentialsModel:
    """Credentials for authenticating to the specified Active Directory objects.

    Attributes:
        use_master_credentials (bool): If `true`, master credentials are used for authenticating with the specified
            Active Directory objects.
        object_ (ADObjectModel): Active Directory object.
        credentials_id (UUID | Unset): Credentials ID.
    """

    use_master_credentials: bool
    object_: ADObjectModel
    credentials_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        use_master_credentials = self.use_master_credentials

        object_ = self.object_.to_dict()

        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "useMasterCredentials": use_master_credentials,
                "object": object_,
            }
        )
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ad_object_model import ADObjectModel

        d = dict(src_dict)
        use_master_credentials = d.pop("useMasterCredentials")

        object_ = ADObjectModel.from_dict(d.pop("object"))

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        ad_object_custom_credentials_model = cls(
            use_master_credentials=use_master_credentials,
            object_=object_,
            credentials_id=credentials_id,
        )

        ad_object_custom_credentials_model.additional_properties = d
        return ad_object_custom_credentials_model

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

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.entra_id_item_include_restore_spec import EntraIDItemIncludeRestoreSpec
    from ..models.entra_id_tenant_restore_user_password_spec import EntraIdTenantRestoreUserPasswordSpec


T = TypeVar("T", bound="EntraIdTenantItemRestoreSpec")


@_attrs_define
class EntraIdTenantItemRestoreSpec:
    """Restore settings for Microsoft Entra ID items.

    Attributes:
        credentials_id (UUID | Unset): ID of the credentials record used for connection to the target tenant. The
            property is used only for delegated restore by a restore operator that does not have access to pre-saved
            credentials. To obtain the credentials, use the following requests&#58; <ol><li>Obtain a user code&#58; [Get
            User Code for Delegated Restore of Microsoft Entra ID
            Items](Restore#operation/GetEntraIdTenantRestoreDeviceCode).</li> <li>Use the user code to get the credentials
            ID&#58; [Get Credentials for Delegated Restore of Microsoft Entra ID
            Items](Restore#operation/GetEntraIdTenantRestoreDeviceCodeState).</li></ol>
        items (list[EntraIDItemIncludeRestoreSpec] | Unset): Array of Microsoft Entra ID items.
        skip_relationships (bool | Unset): If `true`, item relationships (such as assigned roles, group memberships,
            group ownerships, and admin unit memberships) are not restored.
        skip_recycle_bin_restore (bool | Unset): If `true`, all of the items are restored from the backup. <p>Otherwise,
            the items are restored from the Microsoft Entra ID recycle bin. If an item is not found in the recycle bin, it
            will not be restored.</p>
        skip_objects_if_exist (bool | Unset): If `true`, only non-existing items are restored.
        request_password_change_on_logon (bool | Unset): If `true`, restored users will be forced to change their
            passwords after their first logon.
        default_user_password (str | Unset): Default password that will be set for all users.
        users_passwords (list[EntraIdTenantRestoreUserPasswordSpec] | Unset): Array of custom user passwords. To
            generate the passwords, run the [Generate Microsoft Entra ID User Passwords](Backup-
            Browsers#operation/GenerateEntraIdTenantPassword) request.
        reason (str | Unset): Reason for restoring Microsoft Entra ID items.
    """

    credentials_id: UUID | Unset = UNSET
    items: list[EntraIDItemIncludeRestoreSpec] | Unset = UNSET
    skip_relationships: bool | Unset = UNSET
    skip_recycle_bin_restore: bool | Unset = UNSET
    skip_objects_if_exist: bool | Unset = UNSET
    request_password_change_on_logon: bool | Unset = UNSET
    default_user_password: str | Unset = UNSET
    users_passwords: list[EntraIdTenantRestoreUserPasswordSpec] | Unset = UNSET
    reason: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credentials_id: str | Unset = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        items: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.items, Unset):
            items = []
            for items_item_data in self.items:
                items_item = items_item_data.to_dict()
                items.append(items_item)

        skip_relationships = self.skip_relationships

        skip_recycle_bin_restore = self.skip_recycle_bin_restore

        skip_objects_if_exist = self.skip_objects_if_exist

        request_password_change_on_logon = self.request_password_change_on_logon

        default_user_password = self.default_user_password

        users_passwords: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.users_passwords, Unset):
            users_passwords = []
            for users_passwords_item_data in self.users_passwords:
                users_passwords_item = users_passwords_item_data.to_dict()
                users_passwords.append(users_passwords_item)

        reason = self.reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if items is not UNSET:
            field_dict["items"] = items
        if skip_relationships is not UNSET:
            field_dict["skipRelationships"] = skip_relationships
        if skip_recycle_bin_restore is not UNSET:
            field_dict["skipRecycleBinRestore"] = skip_recycle_bin_restore
        if skip_objects_if_exist is not UNSET:
            field_dict["skipObjectsIfExist"] = skip_objects_if_exist
        if request_password_change_on_logon is not UNSET:
            field_dict["requestPasswordChangeOnLogon"] = request_password_change_on_logon
        if default_user_password is not UNSET:
            field_dict["defaultUserPassword"] = default_user_password
        if users_passwords is not UNSET:
            field_dict["usersPasswords"] = users_passwords
        if reason is not UNSET:
            field_dict["reason"] = reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.entra_id_item_include_restore_spec import EntraIDItemIncludeRestoreSpec
        from ..models.entra_id_tenant_restore_user_password_spec import EntraIdTenantRestoreUserPasswordSpec

        d = dict(src_dict)
        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: UUID | Unset
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        _items = d.pop("items", UNSET)
        items: list[EntraIDItemIncludeRestoreSpec] | Unset = UNSET
        if _items is not UNSET:
            items = []
            for items_item_data in _items:
                items_item = EntraIDItemIncludeRestoreSpec.from_dict(items_item_data)

                items.append(items_item)

        skip_relationships = d.pop("skipRelationships", UNSET)

        skip_recycle_bin_restore = d.pop("skipRecycleBinRestore", UNSET)

        skip_objects_if_exist = d.pop("skipObjectsIfExist", UNSET)

        request_password_change_on_logon = d.pop("requestPasswordChangeOnLogon", UNSET)

        default_user_password = d.pop("defaultUserPassword", UNSET)

        _users_passwords = d.pop("usersPasswords", UNSET)
        users_passwords: list[EntraIdTenantRestoreUserPasswordSpec] | Unset = UNSET
        if _users_passwords is not UNSET:
            users_passwords = []
            for users_passwords_item_data in _users_passwords:
                users_passwords_item = EntraIdTenantRestoreUserPasswordSpec.from_dict(users_passwords_item_data)

                users_passwords.append(users_passwords_item)

        reason = d.pop("reason", UNSET)

        entra_id_tenant_item_restore_spec = cls(
            credentials_id=credentials_id,
            items=items,
            skip_relationships=skip_relationships,
            skip_recycle_bin_restore=skip_recycle_bin_restore,
            skip_objects_if_exist=skip_objects_if_exist,
            request_password_change_on_logon=request_password_change_on_logon,
            default_user_password=default_user_password,
            users_passwords=users_passwords,
            reason=reason,
        )

        entra_id_tenant_item_restore_spec.additional_properties = d
        return entra_id_tenant_item_restore_spec

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

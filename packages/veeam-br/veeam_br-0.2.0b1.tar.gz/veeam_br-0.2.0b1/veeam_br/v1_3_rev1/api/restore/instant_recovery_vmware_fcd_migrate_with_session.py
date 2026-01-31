from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.session_model import SessionModel
from ...models.vmware_fcd_quick_migration_spec import VmwareFcdQuickMigrationSpec
from ...types import Response


def _get_kwargs(
    mount_id: UUID,
    *,
    body: VmwareFcdQuickMigrationSpec,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/restore/instantRecovery/vSphere/fcd/{mount_id}/migrate".format(
            mount_id=quote(str(mount_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Error | SessionModel | None:
    if response.status_code == 200:
        response_200 = SessionModel.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = Error.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = Error.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = Error.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Error | SessionModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    mount_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: VmwareFcdQuickMigrationSpec,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | SessionModel]:
    """Start FCD Migration

     The HTTP POST request to the `/api/v1/restore/instantRecovery/vSphere/fcd/{mountId}/migrate`
    endpoint starts migration of FCDs from the specified mount point.<p>In the request body, specify FCD
    migration configuration:<ul> <li>Disks for migration</li> <li>Target datastore</li> <li>Storage
    policy that will be applied to the migrated disks</li></ul> For details on how to get models of the
    datastore and storage policy, see [Get Inventory Objects](Inventory-
    Browser#operation/GetInventoryObjects).<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (VmwareFcdQuickMigrationSpec): Migration settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | SessionModel]
    """

    kwargs = _get_kwargs(
        mount_id=mount_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    mount_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: VmwareFcdQuickMigrationSpec,
    x_api_version: str = "1.3-rev1",
) -> Error | SessionModel | None:
    """Start FCD Migration

     The HTTP POST request to the `/api/v1/restore/instantRecovery/vSphere/fcd/{mountId}/migrate`
    endpoint starts migration of FCDs from the specified mount point.<p>In the request body, specify FCD
    migration configuration:<ul> <li>Disks for migration</li> <li>Target datastore</li> <li>Storage
    policy that will be applied to the migrated disks</li></ul> For details on how to get models of the
    datastore and storage policy, see [Get Inventory Objects](Inventory-
    Browser#operation/GetInventoryObjects).<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (VmwareFcdQuickMigrationSpec): Migration settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | SessionModel
    """

    return sync_detailed(
        mount_id=mount_id,
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    mount_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: VmwareFcdQuickMigrationSpec,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | SessionModel]:
    """Start FCD Migration

     The HTTP POST request to the `/api/v1/restore/instantRecovery/vSphere/fcd/{mountId}/migrate`
    endpoint starts migration of FCDs from the specified mount point.<p>In the request body, specify FCD
    migration configuration:<ul> <li>Disks for migration</li> <li>Target datastore</li> <li>Storage
    policy that will be applied to the migrated disks</li></ul> For details on how to get models of the
    datastore and storage policy, see [Get Inventory Objects](Inventory-
    Browser#operation/GetInventoryObjects).<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (VmwareFcdQuickMigrationSpec): Migration settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | SessionModel]
    """

    kwargs = _get_kwargs(
        mount_id=mount_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    mount_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: VmwareFcdQuickMigrationSpec,
    x_api_version: str = "1.3-rev1",
) -> Error | SessionModel | None:
    """Start FCD Migration

     The HTTP POST request to the `/api/v1/restore/instantRecovery/vSphere/fcd/{mountId}/migrate`
    endpoint starts migration of FCDs from the specified mount point.<p>In the request body, specify FCD
    migration configuration:<ul> <li>Disks for migration</li> <li>Target datastore</li> <li>Storage
    policy that will be applied to the migrated disks</li></ul> For details on how to get models of the
    datastore and storage policy, see [Get Inventory Objects](Inventory-
    Browser#operation/GetInventoryObjects).<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (VmwareFcdQuickMigrationSpec): Migration settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | SessionModel
    """

    return (
        await asyncio_detailed(
            mount_id=mount_id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

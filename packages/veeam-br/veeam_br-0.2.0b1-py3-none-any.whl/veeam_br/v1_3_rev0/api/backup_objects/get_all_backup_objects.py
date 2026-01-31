from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.backup_objects_result import BackupObjectsResult
from ...models.e_backup_objects_filters_order_column import EBackupObjectsFiltersOrderColumn
from ...models.e_platform_type import EPlatformType
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EBackupObjectsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    platform_name_filter: EPlatformType | Unset = UNSET,
    platform_id_filter: UUID | Unset = UNSET,
    type_filter: str | Unset = UNSET,
    vi_type_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    params["skip"] = skip

    params["limit"] = limit

    json_order_column: str | Unset = UNSET
    if not isinstance(order_column, Unset):
        json_order_column = order_column.value

    params["orderColumn"] = json_order_column

    params["orderAsc"] = order_asc

    params["nameFilter"] = name_filter

    json_platform_name_filter: str | Unset = UNSET
    if not isinstance(platform_name_filter, Unset):
        json_platform_name_filter = platform_name_filter.value

    params["platformNameFilter"] = json_platform_name_filter

    json_platform_id_filter: str | Unset = UNSET
    if not isinstance(platform_id_filter, Unset):
        json_platform_id_filter = str(platform_id_filter)
    params["platformIdFilter"] = json_platform_id_filter

    params["typeFilter"] = type_filter

    params["viTypeFilter"] = vi_type_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/backupObjects",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BackupObjectsResult | Error | None:
    if response.status_code == 200:
        response_200 = BackupObjectsResult.from_dict(response.json())

        return response_200

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
) -> Response[BackupObjectsResult | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EBackupObjectsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    platform_name_filter: EPlatformType | Unset = UNSET,
    platform_id_filter: UUID | Unset = UNSET,
    type_filter: str | Unset = UNSET,
    vi_type_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[BackupObjectsResult | Error]:
    """Get All Backup Objects

     The HTTP GET request to the `/api/v1/backupObjects` path allows you to get an array of virtual
    infrastructure objects (VMs and VM containers) that are included in backups created by the backup
    server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore
    Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EBackupObjectsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        platform_name_filter (EPlatformType | Unset): Platform type.
        platform_id_filter (UUID | Unset):
        type_filter (str | Unset):
        vi_type_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BackupObjectsResult | Error]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        platform_name_filter=platform_name_filter,
        platform_id_filter=platform_id_filter,
        type_filter=type_filter,
        vi_type_filter=vi_type_filter,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EBackupObjectsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    platform_name_filter: EPlatformType | Unset = UNSET,
    platform_id_filter: UUID | Unset = UNSET,
    type_filter: str | Unset = UNSET,
    vi_type_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> BackupObjectsResult | Error | None:
    """Get All Backup Objects

     The HTTP GET request to the `/api/v1/backupObjects` path allows you to get an array of virtual
    infrastructure objects (VMs and VM containers) that are included in backups created by the backup
    server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore
    Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EBackupObjectsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        platform_name_filter (EPlatformType | Unset): Platform type.
        platform_id_filter (UUID | Unset):
        type_filter (str | Unset):
        vi_type_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BackupObjectsResult | Error
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        platform_name_filter=platform_name_filter,
        platform_id_filter=platform_id_filter,
        type_filter=type_filter,
        vi_type_filter=vi_type_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EBackupObjectsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    platform_name_filter: EPlatformType | Unset = UNSET,
    platform_id_filter: UUID | Unset = UNSET,
    type_filter: str | Unset = UNSET,
    vi_type_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[BackupObjectsResult | Error]:
    """Get All Backup Objects

     The HTTP GET request to the `/api/v1/backupObjects` path allows you to get an array of virtual
    infrastructure objects (VMs and VM containers) that are included in backups created by the backup
    server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore
    Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EBackupObjectsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        platform_name_filter (EPlatformType | Unset): Platform type.
        platform_id_filter (UUID | Unset):
        type_filter (str | Unset):
        vi_type_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BackupObjectsResult | Error]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        platform_name_filter=platform_name_filter,
        platform_id_filter=platform_id_filter,
        type_filter=type_filter,
        vi_type_filter=vi_type_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EBackupObjectsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    platform_name_filter: EPlatformType | Unset = UNSET,
    platform_id_filter: UUID | Unset = UNSET,
    type_filter: str | Unset = UNSET,
    vi_type_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> BackupObjectsResult | Error | None:
    """Get All Backup Objects

     The HTTP GET request to the `/api/v1/backupObjects` path allows you to get an array of virtual
    infrastructure objects (VMs and VM containers) that are included in backups created by the backup
    server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore
    Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EBackupObjectsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        platform_name_filter (EPlatformType | Unset): Platform type.
        platform_id_filter (UUID | Unset):
        type_filter (str | Unset):
        vi_type_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BackupObjectsResult | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            platform_name_filter=platform_name_filter,
            platform_id_filter=platform_id_filter,
            type_filter=type_filter,
            vi_type_filter=vi_type_filter,
            x_api_version=x_api_version,
        )
    ).parsed

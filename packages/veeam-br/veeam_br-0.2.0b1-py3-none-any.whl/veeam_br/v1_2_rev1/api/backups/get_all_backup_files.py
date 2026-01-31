import datetime
from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.backup_files_result import BackupFilesResult
from ...models.e_backup_file_gfs_period import EBackupFileGFSPeriod
from ...models.e_backup_files_filters_order_column import EBackupFilesFiltersOrderColumn
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: UUID,
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EBackupFilesFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    gfs_period_filter: EBackupFileGFSPeriod | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
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

    json_created_after_filter: str | Unset = UNSET
    if not isinstance(created_after_filter, Unset):
        json_created_after_filter = created_after_filter.isoformat()
    params["createdAfterFilter"] = json_created_after_filter

    json_created_before_filter: str | Unset = UNSET
    if not isinstance(created_before_filter, Unset):
        json_created_before_filter = created_before_filter.isoformat()
    params["createdBeforeFilter"] = json_created_before_filter

    json_gfs_period_filter: str | Unset = UNSET
    if not isinstance(gfs_period_filter, Unset):
        json_gfs_period_filter = gfs_period_filter.value

    params["gfsPeriodFilter"] = json_gfs_period_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/backups/{id}/backupFiles".format(
            id=quote(str(id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BackupFilesResult | Error | None:
    if response.status_code == 200:
        response_200 = BackupFilesResult.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = Error.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = Error.from_dict(response.json())

        return response_403

    if response.status_code == 500:
        response_500 = Error.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[BackupFilesResult | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EBackupFilesFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    gfs_period_filter: EBackupFileGFSPeriod | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[BackupFilesResult | Error]:
    """Get All Backup Files

     The HTTP GET request to the `/api/v1/backups/{id}/backupFiles` path allows you to get an array of
    all backup files in a backup that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer.</p>

    Args:
        id (UUID):
        skip (int | Unset):
        limit (int | Unset):
        order_column (EBackupFilesFiltersOrderColumn | Unset): Sorts backup files by one of the
            backup file parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        gfs_period_filter (EBackupFileGFSPeriod | Unset): GFS flag assigned to the backup file.
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BackupFilesResult | Error]
    """

    kwargs = _get_kwargs(
        id=id,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        gfs_period_filter=gfs_period_filter,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EBackupFilesFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    gfs_period_filter: EBackupFileGFSPeriod | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> BackupFilesResult | Error | None:
    """Get All Backup Files

     The HTTP GET request to the `/api/v1/backups/{id}/backupFiles` path allows you to get an array of
    all backup files in a backup that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer.</p>

    Args:
        id (UUID):
        skip (int | Unset):
        limit (int | Unset):
        order_column (EBackupFilesFiltersOrderColumn | Unset): Sorts backup files by one of the
            backup file parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        gfs_period_filter (EBackupFileGFSPeriod | Unset): GFS flag assigned to the backup file.
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BackupFilesResult | Error
    """

    return sync_detailed(
        id=id,
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        gfs_period_filter=gfs_period_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EBackupFilesFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    gfs_period_filter: EBackupFileGFSPeriod | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[BackupFilesResult | Error]:
    """Get All Backup Files

     The HTTP GET request to the `/api/v1/backups/{id}/backupFiles` path allows you to get an array of
    all backup files in a backup that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer.</p>

    Args:
        id (UUID):
        skip (int | Unset):
        limit (int | Unset):
        order_column (EBackupFilesFiltersOrderColumn | Unset): Sorts backup files by one of the
            backup file parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        gfs_period_filter (EBackupFileGFSPeriod | Unset): GFS flag assigned to the backup file.
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BackupFilesResult | Error]
    """

    kwargs = _get_kwargs(
        id=id,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        gfs_period_filter=gfs_period_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EBackupFilesFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    gfs_period_filter: EBackupFileGFSPeriod | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> BackupFilesResult | Error | None:
    """Get All Backup Files

     The HTTP GET request to the `/api/v1/backups/{id}/backupFiles` path allows you to get an array of
    all backup files in a backup that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer.</p>

    Args:
        id (UUID):
        skip (int | Unset):
        limit (int | Unset):
        order_column (EBackupFilesFiltersOrderColumn | Unset): Sorts backup files by one of the
            backup file parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        gfs_period_filter (EBackupFileGFSPeriod | Unset): GFS flag assigned to the backup file.
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BackupFilesResult | Error
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            created_after_filter=created_after_filter,
            created_before_filter=created_before_filter,
            gfs_period_filter=gfs_period_filter,
            x_api_version=x_api_version,
        )
    ).parsed

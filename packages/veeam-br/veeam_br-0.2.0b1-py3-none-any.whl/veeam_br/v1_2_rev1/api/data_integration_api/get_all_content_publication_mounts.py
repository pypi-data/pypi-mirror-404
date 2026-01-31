from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.backup_content_mounts_result import BackupContentMountsResult
from ...models.e_backup_content_disk_publish_mode import EBackupContentDiskPublishMode
from ...models.e_backup_content_mount_state import EBackupContentMountState
from ...models.e_backup_content_mounts_filters_order_column import EBackupContentMountsFiltersOrderColumn
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EBackupContentMountsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    state_filter: EBackupContentMountState | Unset = UNSET,
    mode_filter: EBackupContentDiskPublishMode | Unset = UNSET,
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

    json_state_filter: str | Unset = UNSET
    if not isinstance(state_filter, Unset):
        json_state_filter = state_filter.value

    params["stateFilter"] = json_state_filter

    json_mode_filter: str | Unset = UNSET
    if not isinstance(mode_filter, Unset):
        json_mode_filter = mode_filter.value

    params["modeFilter"] = json_mode_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/dataIntegration",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BackupContentMountsResult | Error | None:
    if response.status_code == 200:
        response_200 = BackupContentMountsResult.from_dict(response.json())

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
) -> Response[BackupContentMountsResult | Error]:
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
    limit: int | Unset = UNSET,
    order_column: EBackupContentMountsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    state_filter: EBackupContentMountState | Unset = UNSET,
    mode_filter: EBackupContentDiskPublishMode | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[BackupContentMountsResult | Error]:
    """Get All Disk Publishing Mount Points

     The HTTP GET request to the `/api/v1/dataIntegration` path allows you to get an array of mount
    points for disk publishing operations.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Restore Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EBackupContentMountsFiltersOrderColumn | Unset): Sorts mount points by one
            of the mount point parameters.
        order_asc (bool | Unset):
        state_filter (EBackupContentMountState | Unset): Mount state.
        mode_filter (EBackupContentDiskPublishMode | Unset): Disk publishing mount mode.
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BackupContentMountsResult | Error]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        state_filter=state_filter,
        mode_filter=mode_filter,
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
    limit: int | Unset = UNSET,
    order_column: EBackupContentMountsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    state_filter: EBackupContentMountState | Unset = UNSET,
    mode_filter: EBackupContentDiskPublishMode | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> BackupContentMountsResult | Error | None:
    """Get All Disk Publishing Mount Points

     The HTTP GET request to the `/api/v1/dataIntegration` path allows you to get an array of mount
    points for disk publishing operations.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Restore Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EBackupContentMountsFiltersOrderColumn | Unset): Sorts mount points by one
            of the mount point parameters.
        order_asc (bool | Unset):
        state_filter (EBackupContentMountState | Unset): Mount state.
        mode_filter (EBackupContentDiskPublishMode | Unset): Disk publishing mount mode.
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BackupContentMountsResult | Error
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        state_filter=state_filter,
        mode_filter=mode_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EBackupContentMountsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    state_filter: EBackupContentMountState | Unset = UNSET,
    mode_filter: EBackupContentDiskPublishMode | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[BackupContentMountsResult | Error]:
    """Get All Disk Publishing Mount Points

     The HTTP GET request to the `/api/v1/dataIntegration` path allows you to get an array of mount
    points for disk publishing operations.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Restore Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EBackupContentMountsFiltersOrderColumn | Unset): Sorts mount points by one
            of the mount point parameters.
        order_asc (bool | Unset):
        state_filter (EBackupContentMountState | Unset): Mount state.
        mode_filter (EBackupContentDiskPublishMode | Unset): Disk publishing mount mode.
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BackupContentMountsResult | Error]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        state_filter=state_filter,
        mode_filter=mode_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EBackupContentMountsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    state_filter: EBackupContentMountState | Unset = UNSET,
    mode_filter: EBackupContentDiskPublishMode | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> BackupContentMountsResult | Error | None:
    """Get All Disk Publishing Mount Points

     The HTTP GET request to the `/api/v1/dataIntegration` path allows you to get an array of mount
    points for disk publishing operations.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Restore Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EBackupContentMountsFiltersOrderColumn | Unset): Sorts mount points by one
            of the mount point parameters.
        order_asc (bool | Unset):
        state_filter (EBackupContentMountState | Unset): Mount state.
        mode_filter (EBackupContentDiskPublishMode | Unset): Disk publishing mount mode.
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BackupContentMountsResult | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            state_filter=state_filter,
            mode_filter=mode_filter,
            x_api_version=x_api_version,
        )
    ).parsed

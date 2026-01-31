import datetime
from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_platform_type import EPlatformType
from ...models.e_replica_restore_points_filters_order_column import EReplicaRestorePointsFiltersOrderColumn
from ...models.e_suspicious_activity_severity import ESuspiciousActivitySeverity
from ...models.error import Error
from ...models.replica_points_result import ReplicaPointsResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EReplicaRestorePointsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    platform_name_filter: EPlatformType | Unset = UNSET,
    platform_id_filter: UUID | Unset = UNSET,
    replica_id_filter: UUID | Unset = UNSET,
    malware_status_filter: ESuspiciousActivitySeverity | Unset = UNSET,
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

    json_created_after_filter: str | Unset = UNSET
    if not isinstance(created_after_filter, Unset):
        json_created_after_filter = created_after_filter.isoformat()
    params["createdAfterFilter"] = json_created_after_filter

    json_created_before_filter: str | Unset = UNSET
    if not isinstance(created_before_filter, Unset):
        json_created_before_filter = created_before_filter.isoformat()
    params["createdBeforeFilter"] = json_created_before_filter

    params["nameFilter"] = name_filter

    json_platform_name_filter: str | Unset = UNSET
    if not isinstance(platform_name_filter, Unset):
        json_platform_name_filter = platform_name_filter.value

    params["platformNameFilter"] = json_platform_name_filter

    json_platform_id_filter: str | Unset = UNSET
    if not isinstance(platform_id_filter, Unset):
        json_platform_id_filter = str(platform_id_filter)
    params["platformIdFilter"] = json_platform_id_filter

    json_replica_id_filter: str | Unset = UNSET
    if not isinstance(replica_id_filter, Unset):
        json_replica_id_filter = str(replica_id_filter)
    params["replicaIdFilter"] = json_replica_id_filter

    json_malware_status_filter: str | Unset = UNSET
    if not isinstance(malware_status_filter, Unset):
        json_malware_status_filter = malware_status_filter.value

    params["malwareStatusFilter"] = json_malware_status_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/replicaPoints",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | ReplicaPointsResult | None:
    if response.status_code == 200:
        response_200 = ReplicaPointsResult.from_dict(response.json())

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
) -> Response[Error | ReplicaPointsResult]:
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
    order_column: EReplicaRestorePointsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    platform_name_filter: EPlatformType | Unset = UNSET,
    platform_id_filter: UUID | Unset = UNSET,
    replica_id_filter: UUID | Unset = UNSET,
    malware_status_filter: ESuspiciousActivitySeverity | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | ReplicaPointsResult]:
    """Get All Replica Restore Points

     The HTTP GET request to the `/api/v1/replicaRestorePoints` path allows you to get an array of all
    replica restore points created on the backup server.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Restore Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EReplicaRestorePointsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        name_filter (str | Unset):
        platform_name_filter (EPlatformType | Unset): Platform type.
        platform_id_filter (UUID | Unset):
        replica_id_filter (UUID | Unset):
        malware_status_filter (ESuspiciousActivitySeverity | Unset): Malware status.
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | ReplicaPointsResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        name_filter=name_filter,
        platform_name_filter=platform_name_filter,
        platform_id_filter=platform_id_filter,
        replica_id_filter=replica_id_filter,
        malware_status_filter=malware_status_filter,
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
    order_column: EReplicaRestorePointsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    platform_name_filter: EPlatformType | Unset = UNSET,
    platform_id_filter: UUID | Unset = UNSET,
    replica_id_filter: UUID | Unset = UNSET,
    malware_status_filter: ESuspiciousActivitySeverity | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Error | ReplicaPointsResult | None:
    """Get All Replica Restore Points

     The HTTP GET request to the `/api/v1/replicaRestorePoints` path allows you to get an array of all
    replica restore points created on the backup server.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Restore Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EReplicaRestorePointsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        name_filter (str | Unset):
        platform_name_filter (EPlatformType | Unset): Platform type.
        platform_id_filter (UUID | Unset):
        replica_id_filter (UUID | Unset):
        malware_status_filter (ESuspiciousActivitySeverity | Unset): Malware status.
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | ReplicaPointsResult
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        name_filter=name_filter,
        platform_name_filter=platform_name_filter,
        platform_id_filter=platform_id_filter,
        replica_id_filter=replica_id_filter,
        malware_status_filter=malware_status_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EReplicaRestorePointsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    platform_name_filter: EPlatformType | Unset = UNSET,
    platform_id_filter: UUID | Unset = UNSET,
    replica_id_filter: UUID | Unset = UNSET,
    malware_status_filter: ESuspiciousActivitySeverity | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | ReplicaPointsResult]:
    """Get All Replica Restore Points

     The HTTP GET request to the `/api/v1/replicaRestorePoints` path allows you to get an array of all
    replica restore points created on the backup server.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Restore Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EReplicaRestorePointsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        name_filter (str | Unset):
        platform_name_filter (EPlatformType | Unset): Platform type.
        platform_id_filter (UUID | Unset):
        replica_id_filter (UUID | Unset):
        malware_status_filter (ESuspiciousActivitySeverity | Unset): Malware status.
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | ReplicaPointsResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        name_filter=name_filter,
        platform_name_filter=platform_name_filter,
        platform_id_filter=platform_id_filter,
        replica_id_filter=replica_id_filter,
        malware_status_filter=malware_status_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EReplicaRestorePointsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    platform_name_filter: EPlatformType | Unset = UNSET,
    platform_id_filter: UUID | Unset = UNSET,
    replica_id_filter: UUID | Unset = UNSET,
    malware_status_filter: ESuspiciousActivitySeverity | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Error | ReplicaPointsResult | None:
    """Get All Replica Restore Points

     The HTTP GET request to the `/api/v1/replicaRestorePoints` path allows you to get an array of all
    replica restore points created on the backup server.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Restore Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EReplicaRestorePointsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        name_filter (str | Unset):
        platform_name_filter (EPlatformType | Unset): Platform type.
        platform_id_filter (UUID | Unset):
        replica_id_filter (UUID | Unset):
        malware_status_filter (ESuspiciousActivitySeverity | Unset): Malware status.
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | ReplicaPointsResult
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            created_after_filter=created_after_filter,
            created_before_filter=created_before_filter,
            name_filter=name_filter,
            platform_name_filter=platform_name_filter,
            platform_id_filter=platform_id_filter,
            replica_id_filter=replica_id_filter,
            malware_status_filter=malware_status_filter,
            x_api_version=x_api_version,
        )
    ).parsed

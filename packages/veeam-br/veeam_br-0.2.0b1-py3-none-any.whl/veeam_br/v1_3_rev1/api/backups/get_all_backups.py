import datetime
from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.backups_result import BackupsResult
from ...models.e_backups_filters_order_column import EBackupsFiltersOrderColumn
from ...models.e_job_type import EJobType
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EBackupsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    platform_id_filter: UUID | Unset = UNSET,
    job_id_filter: UUID | Unset = UNSET,
    policy_tag_filter: str | Unset = UNSET,
    job_type_filter: EJobType | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
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

    json_platform_id_filter: str | Unset = UNSET
    if not isinstance(platform_id_filter, Unset):
        json_platform_id_filter = str(platform_id_filter)
    params["platformIdFilter"] = json_platform_id_filter

    json_job_id_filter: str | Unset = UNSET
    if not isinstance(job_id_filter, Unset):
        json_job_id_filter = str(job_id_filter)
    params["jobIdFilter"] = json_job_id_filter

    params["policyTagFilter"] = policy_tag_filter

    json_job_type_filter: str | Unset = UNSET
    if not isinstance(job_type_filter, Unset):
        json_job_type_filter = job_type_filter.value

    params["jobTypeFilter"] = json_job_type_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/backups",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> BackupsResult | Error | None:
    if response.status_code == 200:
        response_200 = BackupsResult.from_dict(response.json())

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
) -> Response[BackupsResult | Error]:
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
    order_column: EBackupsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    platform_id_filter: UUID | Unset = UNSET,
    job_id_filter: UUID | Unset = UNSET,
    policy_tag_filter: str | Unset = UNSET,
    job_type_filter: EJobType | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[BackupsResult | Error]:
    """Get All Backups

     The HTTP GET request to the `/api/v1/backups` endpoint gets an array of all backups that are created
    on or imported to the backup server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator, Veeam Security
    Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EBackupsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        platform_id_filter (UUID | Unset):
        job_id_filter (UUID | Unset):
        policy_tag_filter (str | Unset):
        job_type_filter (EJobType | Unset): Type of the job.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BackupsResult | Error]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        platform_id_filter=platform_id_filter,
        job_id_filter=job_id_filter,
        policy_tag_filter=policy_tag_filter,
        job_type_filter=job_type_filter,
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
    order_column: EBackupsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    platform_id_filter: UUID | Unset = UNSET,
    job_id_filter: UUID | Unset = UNSET,
    policy_tag_filter: str | Unset = UNSET,
    job_type_filter: EJobType | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> BackupsResult | Error | None:
    """Get All Backups

     The HTTP GET request to the `/api/v1/backups` endpoint gets an array of all backups that are created
    on or imported to the backup server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator, Veeam Security
    Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EBackupsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        platform_id_filter (UUID | Unset):
        job_id_filter (UUID | Unset):
        policy_tag_filter (str | Unset):
        job_type_filter (EJobType | Unset): Type of the job.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BackupsResult | Error
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        platform_id_filter=platform_id_filter,
        job_id_filter=job_id_filter,
        policy_tag_filter=policy_tag_filter,
        job_type_filter=job_type_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EBackupsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    platform_id_filter: UUID | Unset = UNSET,
    job_id_filter: UUID | Unset = UNSET,
    policy_tag_filter: str | Unset = UNSET,
    job_type_filter: EJobType | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[BackupsResult | Error]:
    """Get All Backups

     The HTTP GET request to the `/api/v1/backups` endpoint gets an array of all backups that are created
    on or imported to the backup server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator, Veeam Security
    Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EBackupsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        platform_id_filter (UUID | Unset):
        job_id_filter (UUID | Unset):
        policy_tag_filter (str | Unset):
        job_type_filter (EJobType | Unset): Type of the job.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BackupsResult | Error]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        platform_id_filter=platform_id_filter,
        job_id_filter=job_id_filter,
        policy_tag_filter=policy_tag_filter,
        job_type_filter=job_type_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EBackupsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    platform_id_filter: UUID | Unset = UNSET,
    job_id_filter: UUID | Unset = UNSET,
    policy_tag_filter: str | Unset = UNSET,
    job_type_filter: EJobType | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> BackupsResult | Error | None:
    """Get All Backups

     The HTTP GET request to the `/api/v1/backups` endpoint gets an array of all backups that are created
    on or imported to the backup server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator, Veeam Security
    Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EBackupsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        platform_id_filter (UUID | Unset):
        job_id_filter (UUID | Unset):
        policy_tag_filter (str | Unset):
        job_type_filter (EJobType | Unset): Type of the job.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BackupsResult | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            created_after_filter=created_after_filter,
            created_before_filter=created_before_filter,
            platform_id_filter=platform_id_filter,
            job_id_filter=job_id_filter,
            policy_tag_filter=policy_tag_filter,
            job_type_filter=job_type_filter,
            x_api_version=x_api_version,
        )
    ).parsed

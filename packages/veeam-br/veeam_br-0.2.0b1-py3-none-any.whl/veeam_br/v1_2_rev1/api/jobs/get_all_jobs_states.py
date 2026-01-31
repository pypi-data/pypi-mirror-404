import datetime
from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_job_states_filters_order_column import EJobStatesFiltersOrderColumn
from ...models.e_job_status import EJobStatus
from ...models.e_job_type import EJobType
from ...models.e_job_workload import EJobWorkload
from ...models.e_session_result import ESessionResult
from ...models.error import Error
from ...models.job_states_result import JobStatesResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EJobStatesFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    id_filter: UUID | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: EJobType | Unset = UNSET,
    last_result_filter: ESessionResult | Unset = UNSET,
    status_filter: EJobStatus | Unset = UNSET,
    workload_filter: EJobWorkload | Unset = UNSET,
    last_run_after_filter: datetime.datetime | Unset = UNSET,
    last_run_before_filter: datetime.datetime | Unset = UNSET,
    is_high_priority_job_filter: bool | Unset = UNSET,
    repository_id_filter: UUID | Unset = UNSET,
    objects_count_filter: int | Unset = UNSET,
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

    json_id_filter: str | Unset = UNSET
    if not isinstance(id_filter, Unset):
        json_id_filter = str(id_filter)
    params["idFilter"] = json_id_filter

    params["nameFilter"] = name_filter

    json_type_filter: str | Unset = UNSET
    if not isinstance(type_filter, Unset):
        json_type_filter = type_filter.value

    params["typeFilter"] = json_type_filter

    json_last_result_filter: str | Unset = UNSET
    if not isinstance(last_result_filter, Unset):
        json_last_result_filter = last_result_filter.value

    params["lastResultFilter"] = json_last_result_filter

    json_status_filter: str | Unset = UNSET
    if not isinstance(status_filter, Unset):
        json_status_filter = status_filter.value

    params["statusFilter"] = json_status_filter

    json_workload_filter: str | Unset = UNSET
    if not isinstance(workload_filter, Unset):
        json_workload_filter = workload_filter.value

    params["workloadFilter"] = json_workload_filter

    json_last_run_after_filter: str | Unset = UNSET
    if not isinstance(last_run_after_filter, Unset):
        json_last_run_after_filter = last_run_after_filter.isoformat()
    params["lastRunAfterFilter"] = json_last_run_after_filter

    json_last_run_before_filter: str | Unset = UNSET
    if not isinstance(last_run_before_filter, Unset):
        json_last_run_before_filter = last_run_before_filter.isoformat()
    params["lastRunBeforeFilter"] = json_last_run_before_filter

    params["isHighPriorityJobFilter"] = is_high_priority_job_filter

    json_repository_id_filter: str | Unset = UNSET
    if not isinstance(repository_id_filter, Unset):
        json_repository_id_filter = str(repository_id_filter)
    params["repositoryIdFilter"] = json_repository_id_filter

    params["objectsCountFilter"] = objects_count_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/jobs/states",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | JobStatesResult | None:
    if response.status_code == 200:
        response_200 = JobStatesResult.from_dict(response.json())

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
) -> Response[Error | JobStatesResult]:
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
    order_column: EJobStatesFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    id_filter: UUID | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: EJobType | Unset = UNSET,
    last_result_filter: ESessionResult | Unset = UNSET,
    status_filter: EJobStatus | Unset = UNSET,
    workload_filter: EJobWorkload | Unset = UNSET,
    last_run_after_filter: datetime.datetime | Unset = UNSET,
    last_run_before_filter: datetime.datetime | Unset = UNSET,
    is_high_priority_job_filter: bool | Unset = UNSET,
    repository_id_filter: UUID | Unset = UNSET,
    objects_count_filter: int | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | JobStatesResult]:
    """Get All Job States

     The HTTP GET request to the `/api/v1/jobs/states` path allows you to get an array of all job states.
    The states include brief job information that you can also find under the **Jobs** node in the Veeam
    Backup & Replication console.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup
    Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EJobStatesFiltersOrderColumn | Unset): Orders job states by the specified
            column.
        order_asc (bool | Unset):
        id_filter (UUID | Unset):
        name_filter (str | Unset):
        type_filter (EJobType | Unset): Type of the job.
        last_result_filter (ESessionResult | Unset): Result status.
        status_filter (EJobStatus | Unset): Current status of the job.
        workload_filter (EJobWorkload | Unset): Workload which the job must process.
        last_run_after_filter (datetime.datetime | Unset):
        last_run_before_filter (datetime.datetime | Unset):
        is_high_priority_job_filter (bool | Unset):
        repository_id_filter (UUID | Unset):
        objects_count_filter (int | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | JobStatesResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        id_filter=id_filter,
        name_filter=name_filter,
        type_filter=type_filter,
        last_result_filter=last_result_filter,
        status_filter=status_filter,
        workload_filter=workload_filter,
        last_run_after_filter=last_run_after_filter,
        last_run_before_filter=last_run_before_filter,
        is_high_priority_job_filter=is_high_priority_job_filter,
        repository_id_filter=repository_id_filter,
        objects_count_filter=objects_count_filter,
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
    order_column: EJobStatesFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    id_filter: UUID | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: EJobType | Unset = UNSET,
    last_result_filter: ESessionResult | Unset = UNSET,
    status_filter: EJobStatus | Unset = UNSET,
    workload_filter: EJobWorkload | Unset = UNSET,
    last_run_after_filter: datetime.datetime | Unset = UNSET,
    last_run_before_filter: datetime.datetime | Unset = UNSET,
    is_high_priority_job_filter: bool | Unset = UNSET,
    repository_id_filter: UUID | Unset = UNSET,
    objects_count_filter: int | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Error | JobStatesResult | None:
    """Get All Job States

     The HTTP GET request to the `/api/v1/jobs/states` path allows you to get an array of all job states.
    The states include brief job information that you can also find under the **Jobs** node in the Veeam
    Backup & Replication console.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup
    Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EJobStatesFiltersOrderColumn | Unset): Orders job states by the specified
            column.
        order_asc (bool | Unset):
        id_filter (UUID | Unset):
        name_filter (str | Unset):
        type_filter (EJobType | Unset): Type of the job.
        last_result_filter (ESessionResult | Unset): Result status.
        status_filter (EJobStatus | Unset): Current status of the job.
        workload_filter (EJobWorkload | Unset): Workload which the job must process.
        last_run_after_filter (datetime.datetime | Unset):
        last_run_before_filter (datetime.datetime | Unset):
        is_high_priority_job_filter (bool | Unset):
        repository_id_filter (UUID | Unset):
        objects_count_filter (int | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | JobStatesResult
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        id_filter=id_filter,
        name_filter=name_filter,
        type_filter=type_filter,
        last_result_filter=last_result_filter,
        status_filter=status_filter,
        workload_filter=workload_filter,
        last_run_after_filter=last_run_after_filter,
        last_run_before_filter=last_run_before_filter,
        is_high_priority_job_filter=is_high_priority_job_filter,
        repository_id_filter=repository_id_filter,
        objects_count_filter=objects_count_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EJobStatesFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    id_filter: UUID | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: EJobType | Unset = UNSET,
    last_result_filter: ESessionResult | Unset = UNSET,
    status_filter: EJobStatus | Unset = UNSET,
    workload_filter: EJobWorkload | Unset = UNSET,
    last_run_after_filter: datetime.datetime | Unset = UNSET,
    last_run_before_filter: datetime.datetime | Unset = UNSET,
    is_high_priority_job_filter: bool | Unset = UNSET,
    repository_id_filter: UUID | Unset = UNSET,
    objects_count_filter: int | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | JobStatesResult]:
    """Get All Job States

     The HTTP GET request to the `/api/v1/jobs/states` path allows you to get an array of all job states.
    The states include brief job information that you can also find under the **Jobs** node in the Veeam
    Backup & Replication console.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup
    Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EJobStatesFiltersOrderColumn | Unset): Orders job states by the specified
            column.
        order_asc (bool | Unset):
        id_filter (UUID | Unset):
        name_filter (str | Unset):
        type_filter (EJobType | Unset): Type of the job.
        last_result_filter (ESessionResult | Unset): Result status.
        status_filter (EJobStatus | Unset): Current status of the job.
        workload_filter (EJobWorkload | Unset): Workload which the job must process.
        last_run_after_filter (datetime.datetime | Unset):
        last_run_before_filter (datetime.datetime | Unset):
        is_high_priority_job_filter (bool | Unset):
        repository_id_filter (UUID | Unset):
        objects_count_filter (int | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | JobStatesResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        id_filter=id_filter,
        name_filter=name_filter,
        type_filter=type_filter,
        last_result_filter=last_result_filter,
        status_filter=status_filter,
        workload_filter=workload_filter,
        last_run_after_filter=last_run_after_filter,
        last_run_before_filter=last_run_before_filter,
        is_high_priority_job_filter=is_high_priority_job_filter,
        repository_id_filter=repository_id_filter,
        objects_count_filter=objects_count_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EJobStatesFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    id_filter: UUID | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: EJobType | Unset = UNSET,
    last_result_filter: ESessionResult | Unset = UNSET,
    status_filter: EJobStatus | Unset = UNSET,
    workload_filter: EJobWorkload | Unset = UNSET,
    last_run_after_filter: datetime.datetime | Unset = UNSET,
    last_run_before_filter: datetime.datetime | Unset = UNSET,
    is_high_priority_job_filter: bool | Unset = UNSET,
    repository_id_filter: UUID | Unset = UNSET,
    objects_count_filter: int | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Error | JobStatesResult | None:
    """Get All Job States

     The HTTP GET request to the `/api/v1/jobs/states` path allows you to get an array of all job states.
    The states include brief job information that you can also find under the **Jobs** node in the Veeam
    Backup & Replication console.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup
    Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EJobStatesFiltersOrderColumn | Unset): Orders job states by the specified
            column.
        order_asc (bool | Unset):
        id_filter (UUID | Unset):
        name_filter (str | Unset):
        type_filter (EJobType | Unset): Type of the job.
        last_result_filter (ESessionResult | Unset): Result status.
        status_filter (EJobStatus | Unset): Current status of the job.
        workload_filter (EJobWorkload | Unset): Workload which the job must process.
        last_run_after_filter (datetime.datetime | Unset):
        last_run_before_filter (datetime.datetime | Unset):
        is_high_priority_job_filter (bool | Unset):
        repository_id_filter (UUID | Unset):
        objects_count_filter (int | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | JobStatesResult
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            id_filter=id_filter,
            name_filter=name_filter,
            type_filter=type_filter,
            last_result_filter=last_result_filter,
            status_filter=status_filter,
            workload_filter=workload_filter,
            last_run_after_filter=last_run_after_filter,
            last_run_before_filter=last_run_before_filter,
            is_high_priority_job_filter=is_high_priority_job_filter,
            repository_id_filter=repository_id_filter,
            objects_count_filter=objects_count_filter,
            x_api_version=x_api_version,
        )
    ).parsed

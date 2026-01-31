import datetime
from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_antivirus_scan_result import EAntivirusScanResult
from ...models.e_antivirus_scan_state import EAntivirusScanState
from ...models.e_antivirus_scan_type import EAntivirusScanType
from ...models.e_session_result import ESessionResult
from ...models.e_session_state import ESessionState
from ...models.e_session_type import ESessionType
from ...models.e_task_session_type import ETaskSessionType
from ...models.e_task_sessions_filters_order_column import ETaskSessionsFiltersOrderColumn
from ...models.error import Error
from ...models.task_sessions_result import TaskSessionsResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: UUID,
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: ETaskSessionsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: ETaskSessionType | Unset = UNSET,
    session_type_filter: ESessionType | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    ended_after_filter: datetime.datetime | Unset = UNSET,
    ended_before_filter: datetime.datetime | Unset = UNSET,
    state_filter: ESessionState | Unset = UNSET,
    result_filter: ESessionResult | Unset = UNSET,
    scan_type_filter: EAntivirusScanType | Unset = UNSET,
    scan_result_filter: EAntivirusScanResult | Unset = UNSET,
    scan_state_filter: EAntivirusScanState | Unset = UNSET,
    session_id_filter: UUID | Unset = UNSET,
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

    json_type_filter: str | Unset = UNSET
    if not isinstance(type_filter, Unset):
        json_type_filter = type_filter.value

    params["typeFilter"] = json_type_filter

    json_session_type_filter: str | Unset = UNSET
    if not isinstance(session_type_filter, Unset):
        json_session_type_filter = session_type_filter.value

    params["sessionTypeFilter"] = json_session_type_filter

    json_created_after_filter: str | Unset = UNSET
    if not isinstance(created_after_filter, Unset):
        json_created_after_filter = created_after_filter.isoformat()
    params["createdAfterFilter"] = json_created_after_filter

    json_created_before_filter: str | Unset = UNSET
    if not isinstance(created_before_filter, Unset):
        json_created_before_filter = created_before_filter.isoformat()
    params["createdBeforeFilter"] = json_created_before_filter

    json_ended_after_filter: str | Unset = UNSET
    if not isinstance(ended_after_filter, Unset):
        json_ended_after_filter = ended_after_filter.isoformat()
    params["endedAfterFilter"] = json_ended_after_filter

    json_ended_before_filter: str | Unset = UNSET
    if not isinstance(ended_before_filter, Unset):
        json_ended_before_filter = ended_before_filter.isoformat()
    params["endedBeforeFilter"] = json_ended_before_filter

    json_state_filter: str | Unset = UNSET
    if not isinstance(state_filter, Unset):
        json_state_filter = state_filter.value

    params["stateFilter"] = json_state_filter

    json_result_filter: str | Unset = UNSET
    if not isinstance(result_filter, Unset):
        json_result_filter = result_filter.value

    params["resultFilter"] = json_result_filter

    json_scan_type_filter: str | Unset = UNSET
    if not isinstance(scan_type_filter, Unset):
        json_scan_type_filter = scan_type_filter.value

    params["scanTypeFilter"] = json_scan_type_filter

    json_scan_result_filter: str | Unset = UNSET
    if not isinstance(scan_result_filter, Unset):
        json_scan_result_filter = scan_result_filter.value

    params["scanResultFilter"] = json_scan_result_filter

    json_scan_state_filter: str | Unset = UNSET
    if not isinstance(scan_state_filter, Unset):
        json_scan_state_filter = scan_state_filter.value

    params["scanStateFilter"] = json_scan_state_filter

    json_session_id_filter: str | Unset = UNSET
    if not isinstance(session_id_filter, Unset):
        json_session_id_filter = str(session_id_filter)
    params["sessionIdFilter"] = json_session_id_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/sessions/{id}/taskSessions".format(
            id=quote(str(id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | TaskSessionsResult | None:
    if response.status_code == 200:
        response_200 = TaskSessionsResult.from_dict(response.json())

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
) -> Response[Error | TaskSessionsResult]:
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
    limit: int | Unset = 200,
    order_column: ETaskSessionsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: ETaskSessionType | Unset = UNSET,
    session_type_filter: ESessionType | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    ended_after_filter: datetime.datetime | Unset = UNSET,
    ended_before_filter: datetime.datetime | Unset = UNSET,
    state_filter: ESessionState | Unset = UNSET,
    result_filter: ESessionResult | Unset = UNSET,
    scan_type_filter: EAntivirusScanType | Unset = UNSET,
    scan_result_filter: EAntivirusScanResult | Unset = UNSET,
    scan_state_filter: EAntivirusScanState | Unset = UNSET,
    session_id_filter: UUID | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | TaskSessionsResult]:
    """Get Task Sessions For Specified Session

     The HTTP GET request to the `/api/v1/sessions/{id}/taskSessions` endpoint gets an array of task
    sessions performed on the backup server for the session that has the specified `id` .<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape
    Operator, Veeam Backup Viewer.</p>

    Args:
        id (UUID):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (ETaskSessionsFiltersOrderColumn | Unset): Sorts task sessions according to
            one of the parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (ETaskSessionType | Unset): Task session type.
        session_type_filter (ESessionType | Unset): Type of the session.
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        ended_after_filter (datetime.datetime | Unset):
        ended_before_filter (datetime.datetime | Unset):
        state_filter (ESessionState | Unset): State of the session.
        result_filter (ESessionResult | Unset): Result status.
        scan_type_filter (EAntivirusScanType | Unset): Type of antivirus scan.
        scan_result_filter (EAntivirusScanResult | Unset): Antivirus scan result.
        scan_state_filter (EAntivirusScanState | Unset): State of the antivirus scan.
        session_id_filter (UUID | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | TaskSessionsResult]
    """

    kwargs = _get_kwargs(
        id=id,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        type_filter=type_filter,
        session_type_filter=session_type_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        ended_after_filter=ended_after_filter,
        ended_before_filter=ended_before_filter,
        state_filter=state_filter,
        result_filter=result_filter,
        scan_type_filter=scan_type_filter,
        scan_result_filter=scan_result_filter,
        scan_state_filter=scan_state_filter,
        session_id_filter=session_id_filter,
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
    limit: int | Unset = 200,
    order_column: ETaskSessionsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: ETaskSessionType | Unset = UNSET,
    session_type_filter: ESessionType | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    ended_after_filter: datetime.datetime | Unset = UNSET,
    ended_before_filter: datetime.datetime | Unset = UNSET,
    state_filter: ESessionState | Unset = UNSET,
    result_filter: ESessionResult | Unset = UNSET,
    scan_type_filter: EAntivirusScanType | Unset = UNSET,
    scan_result_filter: EAntivirusScanResult | Unset = UNSET,
    scan_state_filter: EAntivirusScanState | Unset = UNSET,
    session_id_filter: UUID | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Error | TaskSessionsResult | None:
    """Get Task Sessions For Specified Session

     The HTTP GET request to the `/api/v1/sessions/{id}/taskSessions` endpoint gets an array of task
    sessions performed on the backup server for the session that has the specified `id` .<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape
    Operator, Veeam Backup Viewer.</p>

    Args:
        id (UUID):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (ETaskSessionsFiltersOrderColumn | Unset): Sorts task sessions according to
            one of the parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (ETaskSessionType | Unset): Task session type.
        session_type_filter (ESessionType | Unset): Type of the session.
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        ended_after_filter (datetime.datetime | Unset):
        ended_before_filter (datetime.datetime | Unset):
        state_filter (ESessionState | Unset): State of the session.
        result_filter (ESessionResult | Unset): Result status.
        scan_type_filter (EAntivirusScanType | Unset): Type of antivirus scan.
        scan_result_filter (EAntivirusScanResult | Unset): Antivirus scan result.
        scan_state_filter (EAntivirusScanState | Unset): State of the antivirus scan.
        session_id_filter (UUID | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | TaskSessionsResult
    """

    return sync_detailed(
        id=id,
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        type_filter=type_filter,
        session_type_filter=session_type_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        ended_after_filter=ended_after_filter,
        ended_before_filter=ended_before_filter,
        state_filter=state_filter,
        result_filter=result_filter,
        scan_type_filter=scan_type_filter,
        scan_result_filter=scan_result_filter,
        scan_state_filter=scan_state_filter,
        session_id_filter=session_id_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: ETaskSessionsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: ETaskSessionType | Unset = UNSET,
    session_type_filter: ESessionType | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    ended_after_filter: datetime.datetime | Unset = UNSET,
    ended_before_filter: datetime.datetime | Unset = UNSET,
    state_filter: ESessionState | Unset = UNSET,
    result_filter: ESessionResult | Unset = UNSET,
    scan_type_filter: EAntivirusScanType | Unset = UNSET,
    scan_result_filter: EAntivirusScanResult | Unset = UNSET,
    scan_state_filter: EAntivirusScanState | Unset = UNSET,
    session_id_filter: UUID | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | TaskSessionsResult]:
    """Get Task Sessions For Specified Session

     The HTTP GET request to the `/api/v1/sessions/{id}/taskSessions` endpoint gets an array of task
    sessions performed on the backup server for the session that has the specified `id` .<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape
    Operator, Veeam Backup Viewer.</p>

    Args:
        id (UUID):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (ETaskSessionsFiltersOrderColumn | Unset): Sorts task sessions according to
            one of the parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (ETaskSessionType | Unset): Task session type.
        session_type_filter (ESessionType | Unset): Type of the session.
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        ended_after_filter (datetime.datetime | Unset):
        ended_before_filter (datetime.datetime | Unset):
        state_filter (ESessionState | Unset): State of the session.
        result_filter (ESessionResult | Unset): Result status.
        scan_type_filter (EAntivirusScanType | Unset): Type of antivirus scan.
        scan_result_filter (EAntivirusScanResult | Unset): Antivirus scan result.
        scan_state_filter (EAntivirusScanState | Unset): State of the antivirus scan.
        session_id_filter (UUID | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | TaskSessionsResult]
    """

    kwargs = _get_kwargs(
        id=id,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        type_filter=type_filter,
        session_type_filter=session_type_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        ended_after_filter=ended_after_filter,
        ended_before_filter=ended_before_filter,
        state_filter=state_filter,
        result_filter=result_filter,
        scan_type_filter=scan_type_filter,
        scan_result_filter=scan_result_filter,
        scan_state_filter=scan_state_filter,
        session_id_filter=session_id_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: ETaskSessionsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: ETaskSessionType | Unset = UNSET,
    session_type_filter: ESessionType | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    ended_after_filter: datetime.datetime | Unset = UNSET,
    ended_before_filter: datetime.datetime | Unset = UNSET,
    state_filter: ESessionState | Unset = UNSET,
    result_filter: ESessionResult | Unset = UNSET,
    scan_type_filter: EAntivirusScanType | Unset = UNSET,
    scan_result_filter: EAntivirusScanResult | Unset = UNSET,
    scan_state_filter: EAntivirusScanState | Unset = UNSET,
    session_id_filter: UUID | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Error | TaskSessionsResult | None:
    """Get Task Sessions For Specified Session

     The HTTP GET request to the `/api/v1/sessions/{id}/taskSessions` endpoint gets an array of task
    sessions performed on the backup server for the session that has the specified `id` .<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape
    Operator, Veeam Backup Viewer.</p>

    Args:
        id (UUID):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (ETaskSessionsFiltersOrderColumn | Unset): Sorts task sessions according to
            one of the parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (ETaskSessionType | Unset): Task session type.
        session_type_filter (ESessionType | Unset): Type of the session.
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        ended_after_filter (datetime.datetime | Unset):
        ended_before_filter (datetime.datetime | Unset):
        state_filter (ESessionState | Unset): State of the session.
        result_filter (ESessionResult | Unset): Result status.
        scan_type_filter (EAntivirusScanType | Unset): Type of antivirus scan.
        scan_result_filter (EAntivirusScanResult | Unset): Antivirus scan result.
        scan_state_filter (EAntivirusScanState | Unset): State of the antivirus scan.
        session_id_filter (UUID | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | TaskSessionsResult
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
            type_filter=type_filter,
            session_type_filter=session_type_filter,
            created_after_filter=created_after_filter,
            created_before_filter=created_before_filter,
            ended_after_filter=ended_after_filter,
            ended_before_filter=ended_before_filter,
            state_filter=state_filter,
            result_filter=result_filter,
            scan_type_filter=scan_type_filter,
            scan_result_filter=scan_result_filter,
            scan_state_filter=scan_state_filter,
            session_id_filter=session_id_filter,
            x_api_version=x_api_version,
        )
    ).parsed

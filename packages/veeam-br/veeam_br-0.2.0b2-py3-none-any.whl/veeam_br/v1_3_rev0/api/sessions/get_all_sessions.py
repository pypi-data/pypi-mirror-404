import datetime
from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_session_result import ESessionResult
from ...models.e_session_state import ESessionState
from ...models.e_session_type import ESessionType
from ...models.e_sessions_filters_order_column import ESessionsFiltersOrderColumn
from ...models.error import Error
from ...models.sessions_result import SessionsResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: ESessionsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    ended_after_filter: datetime.datetime | Unset = UNSET,
    ended_before_filter: datetime.datetime | Unset = UNSET,
    type_filter: list[ESessionType] | Unset = UNSET,
    state_filter: ESessionState | Unset = UNSET,
    result_filter: list[ESessionResult] | Unset = UNSET,
    job_id_filter: UUID | Unset = UNSET,
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

    json_type_filter: list[str] | Unset = UNSET
    if not isinstance(type_filter, Unset):
        json_type_filter = []
        for type_filter_item_data in type_filter:
            type_filter_item = type_filter_item_data.value
            json_type_filter.append(type_filter_item)

    params["typeFilter"] = json_type_filter

    json_state_filter: str | Unset = UNSET
    if not isinstance(state_filter, Unset):
        json_state_filter = state_filter.value

    params["stateFilter"] = json_state_filter

    json_result_filter: list[str] | Unset = UNSET
    if not isinstance(result_filter, Unset):
        json_result_filter = []
        for result_filter_item_data in result_filter:
            result_filter_item = result_filter_item_data.value
            json_result_filter.append(result_filter_item)

    params["resultFilter"] = json_result_filter

    json_job_id_filter: str | Unset = UNSET
    if not isinstance(job_id_filter, Unset):
        json_job_id_filter = str(job_id_filter)
    params["jobIdFilter"] = json_job_id_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/sessions",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Error | SessionsResult | None:
    if response.status_code == 200:
        response_200 = SessionsResult.from_dict(response.json())

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
) -> Response[Error | SessionsResult]:
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
    order_column: ESessionsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    ended_after_filter: datetime.datetime | Unset = UNSET,
    ended_before_filter: datetime.datetime | Unset = UNSET,
    type_filter: list[ESessionType] | Unset = UNSET,
    state_filter: ESessionState | Unset = UNSET,
    result_filter: list[ESessionResult] | Unset = UNSET,
    job_id_filter: UUID | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | SessionsResult]:
    """Get All Sessions

     The HTTP GET request to the `/api/v1/sessions` path allows you to get an array of sessions performed
    on the backup server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator,
    Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator, Veeam Security Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (ESessionsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        ended_after_filter (datetime.datetime | Unset):
        ended_before_filter (datetime.datetime | Unset):
        type_filter (list[ESessionType] | Unset):
        state_filter (ESessionState | Unset): State of the session.
        result_filter (list[ESessionResult] | Unset):
        job_id_filter (UUID | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | SessionsResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        ended_after_filter=ended_after_filter,
        ended_before_filter=ended_before_filter,
        type_filter=type_filter,
        state_filter=state_filter,
        result_filter=result_filter,
        job_id_filter=job_id_filter,
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
    order_column: ESessionsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    ended_after_filter: datetime.datetime | Unset = UNSET,
    ended_before_filter: datetime.datetime | Unset = UNSET,
    type_filter: list[ESessionType] | Unset = UNSET,
    state_filter: ESessionState | Unset = UNSET,
    result_filter: list[ESessionResult] | Unset = UNSET,
    job_id_filter: UUID | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Error | SessionsResult | None:
    """Get All Sessions

     The HTTP GET request to the `/api/v1/sessions` path allows you to get an array of sessions performed
    on the backup server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator,
    Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator, Veeam Security Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (ESessionsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        ended_after_filter (datetime.datetime | Unset):
        ended_before_filter (datetime.datetime | Unset):
        type_filter (list[ESessionType] | Unset):
        state_filter (ESessionState | Unset): State of the session.
        result_filter (list[ESessionResult] | Unset):
        job_id_filter (UUID | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | SessionsResult
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
        ended_after_filter=ended_after_filter,
        ended_before_filter=ended_before_filter,
        type_filter=type_filter,
        state_filter=state_filter,
        result_filter=result_filter,
        job_id_filter=job_id_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: ESessionsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    ended_after_filter: datetime.datetime | Unset = UNSET,
    ended_before_filter: datetime.datetime | Unset = UNSET,
    type_filter: list[ESessionType] | Unset = UNSET,
    state_filter: ESessionState | Unset = UNSET,
    result_filter: list[ESessionResult] | Unset = UNSET,
    job_id_filter: UUID | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | SessionsResult]:
    """Get All Sessions

     The HTTP GET request to the `/api/v1/sessions` path allows you to get an array of sessions performed
    on the backup server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator,
    Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator, Veeam Security Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (ESessionsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        ended_after_filter (datetime.datetime | Unset):
        ended_before_filter (datetime.datetime | Unset):
        type_filter (list[ESessionType] | Unset):
        state_filter (ESessionState | Unset): State of the session.
        result_filter (list[ESessionResult] | Unset):
        job_id_filter (UUID | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | SessionsResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        ended_after_filter=ended_after_filter,
        ended_before_filter=ended_before_filter,
        type_filter=type_filter,
        state_filter=state_filter,
        result_filter=result_filter,
        job_id_filter=job_id_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: ESessionsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    ended_after_filter: datetime.datetime | Unset = UNSET,
    ended_before_filter: datetime.datetime | Unset = UNSET,
    type_filter: list[ESessionType] | Unset = UNSET,
    state_filter: ESessionState | Unset = UNSET,
    result_filter: list[ESessionResult] | Unset = UNSET,
    job_id_filter: UUID | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Error | SessionsResult | None:
    """Get All Sessions

     The HTTP GET request to the `/api/v1/sessions` path allows you to get an array of sessions performed
    on the backup server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator,
    Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator, Veeam Security Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (ESessionsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        ended_after_filter (datetime.datetime | Unset):
        ended_before_filter (datetime.datetime | Unset):
        type_filter (list[ESessionType] | Unset):
        state_filter (ESessionState | Unset): State of the session.
        result_filter (list[ESessionResult] | Unset):
        job_id_filter (UUID | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | SessionsResult
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
            ended_after_filter=ended_after_filter,
            ended_before_filter=ended_before_filter,
            type_filter=type_filter,
            state_filter=state_filter,
            result_filter=result_filter,
            job_id_filter=job_id_filter,
            x_api_version=x_api_version,
        )
    ).parsed

from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_repository_states_filters_order_column import ERepositoryStatesFiltersOrderColumn
from ...models.e_repository_type import ERepositoryType
from ...models.error import Error
from ...models.repository_states_result import RepositoryStatesResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: ERepositoryStatesFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    id_filter: UUID | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: ERepositoryType | Unset = UNSET,
    capacity_filter: float | Unset = UNSET,
    free_space_filter: float | Unset = UNSET,
    used_space_filter: float | Unset = UNSET,
    is_online_filter: bool | Unset = UNSET,
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

    params["capacityFilter"] = capacity_filter

    params["freeSpaceFilter"] = free_space_filter

    params["usedSpaceFilter"] = used_space_filter

    params["isOnlineFilter"] = is_online_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/backupInfrastructure/repositories/states",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | RepositoryStatesResult | None:
    if response.status_code == 200:
        response_200 = RepositoryStatesResult.from_dict(response.json())

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
) -> Response[Error | RepositoryStatesResult]:
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
    order_column: ERepositoryStatesFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    id_filter: UUID | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: ERepositoryType | Unset = UNSET,
    capacity_filter: float | Unset = UNSET,
    free_space_filter: float | Unset = UNSET,
    used_space_filter: float | Unset = UNSET,
    is_online_filter: bool | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | RepositoryStatesResult]:
    """Get All Repository States

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories/states` path allows you to
    get an array of all repository states. The states include repository location and brief statistics,
    such as repository capacity, free and used space.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (ERepositoryStatesFiltersOrderColumn | Unset): Orders repositories by the
            specified column.
        order_asc (bool | Unset):
        id_filter (UUID | Unset):
        name_filter (str | Unset):
        type_filter (ERepositoryType | Unset): Repository type.
        capacity_filter (float | Unset):
        free_space_filter (float | Unset):
        used_space_filter (float | Unset):
        is_online_filter (bool | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | RepositoryStatesResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        id_filter=id_filter,
        name_filter=name_filter,
        type_filter=type_filter,
        capacity_filter=capacity_filter,
        free_space_filter=free_space_filter,
        used_space_filter=used_space_filter,
        is_online_filter=is_online_filter,
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
    order_column: ERepositoryStatesFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    id_filter: UUID | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: ERepositoryType | Unset = UNSET,
    capacity_filter: float | Unset = UNSET,
    free_space_filter: float | Unset = UNSET,
    used_space_filter: float | Unset = UNSET,
    is_online_filter: bool | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Error | RepositoryStatesResult | None:
    """Get All Repository States

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories/states` path allows you to
    get an array of all repository states. The states include repository location and brief statistics,
    such as repository capacity, free and used space.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (ERepositoryStatesFiltersOrderColumn | Unset): Orders repositories by the
            specified column.
        order_asc (bool | Unset):
        id_filter (UUID | Unset):
        name_filter (str | Unset):
        type_filter (ERepositoryType | Unset): Repository type.
        capacity_filter (float | Unset):
        free_space_filter (float | Unset):
        used_space_filter (float | Unset):
        is_online_filter (bool | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | RepositoryStatesResult
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
        capacity_filter=capacity_filter,
        free_space_filter=free_space_filter,
        used_space_filter=used_space_filter,
        is_online_filter=is_online_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: ERepositoryStatesFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    id_filter: UUID | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: ERepositoryType | Unset = UNSET,
    capacity_filter: float | Unset = UNSET,
    free_space_filter: float | Unset = UNSET,
    used_space_filter: float | Unset = UNSET,
    is_online_filter: bool | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | RepositoryStatesResult]:
    """Get All Repository States

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories/states` path allows you to
    get an array of all repository states. The states include repository location and brief statistics,
    such as repository capacity, free and used space.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (ERepositoryStatesFiltersOrderColumn | Unset): Orders repositories by the
            specified column.
        order_asc (bool | Unset):
        id_filter (UUID | Unset):
        name_filter (str | Unset):
        type_filter (ERepositoryType | Unset): Repository type.
        capacity_filter (float | Unset):
        free_space_filter (float | Unset):
        used_space_filter (float | Unset):
        is_online_filter (bool | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | RepositoryStatesResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        id_filter=id_filter,
        name_filter=name_filter,
        type_filter=type_filter,
        capacity_filter=capacity_filter,
        free_space_filter=free_space_filter,
        used_space_filter=used_space_filter,
        is_online_filter=is_online_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: ERepositoryStatesFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    id_filter: UUID | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: ERepositoryType | Unset = UNSET,
    capacity_filter: float | Unset = UNSET,
    free_space_filter: float | Unset = UNSET,
    used_space_filter: float | Unset = UNSET,
    is_online_filter: bool | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Error | RepositoryStatesResult | None:
    """Get All Repository States

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories/states` path allows you to
    get an array of all repository states. The states include repository location and brief statistics,
    such as repository capacity, free and used space.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (ERepositoryStatesFiltersOrderColumn | Unset): Orders repositories by the
            specified column.
        order_asc (bool | Unset):
        id_filter (UUID | Unset):
        name_filter (str | Unset):
        type_filter (ERepositoryType | Unset): Repository type.
        capacity_filter (float | Unset):
        free_space_filter (float | Unset):
        used_space_filter (float | Unset):
        is_online_filter (bool | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | RepositoryStatesResult
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
            capacity_filter=capacity_filter,
            free_space_filter=free_space_filter,
            used_space_filter=used_space_filter,
            is_online_filter=is_online_filter,
            x_api_version=x_api_version,
        )
    ).parsed

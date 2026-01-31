from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_host_updates_state import EHostUpdatesState
from ...models.e_managed_server_state import EManagedServerState
from ...models.e_managed_server_type import EManagedServerType
from ...models.e_managed_servers_filters_order_column import EManagedServersFiltersOrderColumn
from ...models.e_vi_host_type import EViHostType
from ...models.error import Error
from ...models.managed_servers_result import ManagedServersResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EManagedServersFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: list[EManagedServerType] | Unset = UNSET,
    vi_type_filter: EViHostType | Unset = UNSET,
    server_state_filter: EManagedServerState | Unset = UNSET,
    updates_state_filter: list[EHostUpdatesState] | Unset = UNSET,
    include_nested_hosts: bool | Unset = UNSET,
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

    json_type_filter: list[str] | Unset = UNSET
    if not isinstance(type_filter, Unset):
        json_type_filter = []
        for type_filter_item_data in type_filter:
            type_filter_item = type_filter_item_data.value
            json_type_filter.append(type_filter_item)

    params["typeFilter"] = json_type_filter

    json_vi_type_filter: str | Unset = UNSET
    if not isinstance(vi_type_filter, Unset):
        json_vi_type_filter = vi_type_filter.value

    params["viTypeFilter"] = json_vi_type_filter

    json_server_state_filter: str | Unset = UNSET
    if not isinstance(server_state_filter, Unset):
        json_server_state_filter = server_state_filter.value

    params["serverStateFilter"] = json_server_state_filter

    json_updates_state_filter: list[str] | Unset = UNSET
    if not isinstance(updates_state_filter, Unset):
        json_updates_state_filter = []
        for updates_state_filter_item_data in updates_state_filter:
            updates_state_filter_item = updates_state_filter_item_data.value
            json_updates_state_filter.append(updates_state_filter_item)

    params["updatesStateFilter"] = json_updates_state_filter

    params["includeNestedHosts"] = include_nested_hosts

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/backupInfrastructure/managedServers",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | ManagedServersResult | None:
    if response.status_code == 200:
        response_200 = ManagedServersResult.from_dict(response.json())

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
) -> Response[Error | ManagedServersResult]:
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
    order_column: EManagedServersFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: list[EManagedServerType] | Unset = UNSET,
    vi_type_filter: EViHostType | Unset = UNSET,
    server_state_filter: EManagedServerState | Unset = UNSET,
    updates_state_filter: list[EHostUpdatesState] | Unset = UNSET,
    include_nested_hosts: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | ManagedServersResult]:
    """Get All Servers

     The HTTP GET request to the `/api/v1/backupInfrastructure/managedServers` path allows you to get an
    array of all servers that are added to the backup infrastructure.<p> **Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EManagedServersFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (list[EManagedServerType] | Unset):
        vi_type_filter (EViHostType | Unset): Type of the VMware vSphere server.
        server_state_filter (EManagedServerState | Unset): Managed server state.
        updates_state_filter (list[EHostUpdatesState] | Unset):
        include_nested_hosts (bool | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | ManagedServersResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        type_filter=type_filter,
        vi_type_filter=vi_type_filter,
        server_state_filter=server_state_filter,
        updates_state_filter=updates_state_filter,
        include_nested_hosts=include_nested_hosts,
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
    order_column: EManagedServersFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: list[EManagedServerType] | Unset = UNSET,
    vi_type_filter: EViHostType | Unset = UNSET,
    server_state_filter: EManagedServerState | Unset = UNSET,
    updates_state_filter: list[EHostUpdatesState] | Unset = UNSET,
    include_nested_hosts: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Error | ManagedServersResult | None:
    """Get All Servers

     The HTTP GET request to the `/api/v1/backupInfrastructure/managedServers` path allows you to get an
    array of all servers that are added to the backup infrastructure.<p> **Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EManagedServersFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (list[EManagedServerType] | Unset):
        vi_type_filter (EViHostType | Unset): Type of the VMware vSphere server.
        server_state_filter (EManagedServerState | Unset): Managed server state.
        updates_state_filter (list[EHostUpdatesState] | Unset):
        include_nested_hosts (bool | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | ManagedServersResult
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        type_filter=type_filter,
        vi_type_filter=vi_type_filter,
        server_state_filter=server_state_filter,
        updates_state_filter=updates_state_filter,
        include_nested_hosts=include_nested_hosts,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EManagedServersFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: list[EManagedServerType] | Unset = UNSET,
    vi_type_filter: EViHostType | Unset = UNSET,
    server_state_filter: EManagedServerState | Unset = UNSET,
    updates_state_filter: list[EHostUpdatesState] | Unset = UNSET,
    include_nested_hosts: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | ManagedServersResult]:
    """Get All Servers

     The HTTP GET request to the `/api/v1/backupInfrastructure/managedServers` path allows you to get an
    array of all servers that are added to the backup infrastructure.<p> **Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EManagedServersFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (list[EManagedServerType] | Unset):
        vi_type_filter (EViHostType | Unset): Type of the VMware vSphere server.
        server_state_filter (EManagedServerState | Unset): Managed server state.
        updates_state_filter (list[EHostUpdatesState] | Unset):
        include_nested_hosts (bool | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | ManagedServersResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        type_filter=type_filter,
        vi_type_filter=vi_type_filter,
        server_state_filter=server_state_filter,
        updates_state_filter=updates_state_filter,
        include_nested_hosts=include_nested_hosts,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EManagedServersFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: list[EManagedServerType] | Unset = UNSET,
    vi_type_filter: EViHostType | Unset = UNSET,
    server_state_filter: EManagedServerState | Unset = UNSET,
    updates_state_filter: list[EHostUpdatesState] | Unset = UNSET,
    include_nested_hosts: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Error | ManagedServersResult | None:
    """Get All Servers

     The HTTP GET request to the `/api/v1/backupInfrastructure/managedServers` path allows you to get an
    array of all servers that are added to the backup infrastructure.<p> **Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EManagedServersFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (list[EManagedServerType] | Unset):
        vi_type_filter (EViHostType | Unset): Type of the VMware vSphere server.
        server_state_filter (EManagedServerState | Unset): Managed server state.
        updates_state_filter (list[EHostUpdatesState] | Unset):
        include_nested_hosts (bool | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | ManagedServersResult
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            type_filter=type_filter,
            vi_type_filter=vi_type_filter,
            server_state_filter=server_state_filter,
            updates_state_filter=updates_state_filter,
            include_nested_hosts=include_nested_hosts,
            x_api_version=x_api_version,
        )
    ).parsed

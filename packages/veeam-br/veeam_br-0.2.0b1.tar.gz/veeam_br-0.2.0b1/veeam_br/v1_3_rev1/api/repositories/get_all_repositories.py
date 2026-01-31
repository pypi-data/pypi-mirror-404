from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_repository_filters_order_column import ERepositoryFiltersOrderColumn
from ...models.e_repository_type import ERepositoryType
from ...models.error import Error
from ...models.repositories_result import RepositoriesResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: ERepositoryFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: list[ERepositoryType] | Unset = UNSET,
    host_id_filter: UUID | Unset = UNSET,
    path_filter: str | Unset = UNSET,
    vmb_api_filter: str | Unset = UNSET,
    vmb_api_platform: UUID | Unset = UNSET,
    exclude_extents: bool | Unset = UNSET,
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

    json_type_filter: list[str] | Unset = UNSET
    if not isinstance(type_filter, Unset):
        json_type_filter = []
        for type_filter_item_data in type_filter:
            type_filter_item = type_filter_item_data.value
            json_type_filter.append(type_filter_item)

    params["typeFilter"] = json_type_filter

    json_host_id_filter: str | Unset = UNSET
    if not isinstance(host_id_filter, Unset):
        json_host_id_filter = str(host_id_filter)
    params["hostIdFilter"] = json_host_id_filter

    params["pathFilter"] = path_filter

    params["vmbApiFilter"] = vmb_api_filter

    json_vmb_api_platform: str | Unset = UNSET
    if not isinstance(vmb_api_platform, Unset):
        json_vmb_api_platform = str(vmb_api_platform)
    params["vmbApiPlatform"] = json_vmb_api_platform

    params["excludeExtents"] = exclude_extents

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/backupInfrastructure/repositories",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | RepositoriesResult | None:
    if response.status_code == 200:
        response_200 = RepositoriesResult.from_dict(response.json())

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
) -> Response[Error | RepositoriesResult]:
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
    order_column: ERepositoryFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: list[ERepositoryType] | Unset = UNSET,
    host_id_filter: UUID | Unset = UNSET,
    path_filter: str | Unset = UNSET,
    vmb_api_filter: str | Unset = UNSET,
    vmb_api_platform: UUID | Unset = UNSET,
    exclude_extents: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | RepositoriesResult]:
    """Get All Repositories

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories` endpoint gets an array of
    all backup repositories that are added to the backup infrastructure.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (ERepositoryFiltersOrderColumn | Unset): Sorts repositories by one of the
            repository parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (list[ERepositoryType] | Unset):
        host_id_filter (UUID | Unset):
        path_filter (str | Unset):
        vmb_api_filter (str | Unset):
        vmb_api_platform (UUID | Unset):
        exclude_extents (bool | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | RepositoriesResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        type_filter=type_filter,
        host_id_filter=host_id_filter,
        path_filter=path_filter,
        vmb_api_filter=vmb_api_filter,
        vmb_api_platform=vmb_api_platform,
        exclude_extents=exclude_extents,
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
    order_column: ERepositoryFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: list[ERepositoryType] | Unset = UNSET,
    host_id_filter: UUID | Unset = UNSET,
    path_filter: str | Unset = UNSET,
    vmb_api_filter: str | Unset = UNSET,
    vmb_api_platform: UUID | Unset = UNSET,
    exclude_extents: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Error | RepositoriesResult | None:
    """Get All Repositories

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories` endpoint gets an array of
    all backup repositories that are added to the backup infrastructure.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (ERepositoryFiltersOrderColumn | Unset): Sorts repositories by one of the
            repository parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (list[ERepositoryType] | Unset):
        host_id_filter (UUID | Unset):
        path_filter (str | Unset):
        vmb_api_filter (str | Unset):
        vmb_api_platform (UUID | Unset):
        exclude_extents (bool | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | RepositoriesResult
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        type_filter=type_filter,
        host_id_filter=host_id_filter,
        path_filter=path_filter,
        vmb_api_filter=vmb_api_filter,
        vmb_api_platform=vmb_api_platform,
        exclude_extents=exclude_extents,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: ERepositoryFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: list[ERepositoryType] | Unset = UNSET,
    host_id_filter: UUID | Unset = UNSET,
    path_filter: str | Unset = UNSET,
    vmb_api_filter: str | Unset = UNSET,
    vmb_api_platform: UUID | Unset = UNSET,
    exclude_extents: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | RepositoriesResult]:
    """Get All Repositories

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories` endpoint gets an array of
    all backup repositories that are added to the backup infrastructure.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (ERepositoryFiltersOrderColumn | Unset): Sorts repositories by one of the
            repository parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (list[ERepositoryType] | Unset):
        host_id_filter (UUID | Unset):
        path_filter (str | Unset):
        vmb_api_filter (str | Unset):
        vmb_api_platform (UUID | Unset):
        exclude_extents (bool | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | RepositoriesResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        type_filter=type_filter,
        host_id_filter=host_id_filter,
        path_filter=path_filter,
        vmb_api_filter=vmb_api_filter,
        vmb_api_platform=vmb_api_platform,
        exclude_extents=exclude_extents,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: ERepositoryFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: list[ERepositoryType] | Unset = UNSET,
    host_id_filter: UUID | Unset = UNSET,
    path_filter: str | Unset = UNSET,
    vmb_api_filter: str | Unset = UNSET,
    vmb_api_platform: UUID | Unset = UNSET,
    exclude_extents: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Error | RepositoriesResult | None:
    """Get All Repositories

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories` endpoint gets an array of
    all backup repositories that are added to the backup infrastructure.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (ERepositoryFiltersOrderColumn | Unset): Sorts repositories by one of the
            repository parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (list[ERepositoryType] | Unset):
        host_id_filter (UUID | Unset):
        path_filter (str | Unset):
        vmb_api_filter (str | Unset):
        vmb_api_platform (UUID | Unset):
        exclude_extents (bool | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | RepositoriesResult
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
            host_id_filter=host_id_filter,
            path_filter=path_filter,
            vmb_api_filter=vmb_api_filter,
            vmb_api_platform=vmb_api_platform,
            exclude_extents=exclude_extents,
            x_api_version=x_api_version,
        )
    ).parsed

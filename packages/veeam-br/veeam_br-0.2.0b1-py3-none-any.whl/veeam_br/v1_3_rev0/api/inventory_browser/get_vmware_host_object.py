from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_hierarchy_type import EHierarchyType
from ...models.e_vmware_inventory_type import EVmwareInventoryType
from ...models.error import Error
from ...models.ev_centers_inventory_filters_order_column import EvCentersInventoryFiltersOrderColumn
from ...models.v_center_inventory_result import VCenterInventoryResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EvCentersInventoryFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    object_id_filter: str | Unset = UNSET,
    hierarchy_type_filter: EHierarchyType | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: EVmwareInventoryType | Unset = UNSET,
    parent_container_name_filter: str | Unset = UNSET,
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

    params["objectIdFilter"] = object_id_filter

    json_hierarchy_type_filter: str | Unset = UNSET
    if not isinstance(hierarchy_type_filter, Unset):
        json_hierarchy_type_filter = hierarchy_type_filter.value

    params["hierarchyTypeFilter"] = json_hierarchy_type_filter

    params["nameFilter"] = name_filter

    json_type_filter: str | Unset = UNSET
    if not isinstance(type_filter, Unset):
        json_type_filter = type_filter.value

    params["typeFilter"] = json_type_filter

    params["parentContainerNameFilter"] = parent_container_name_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/inventory/vmware/hosts/{name}".format(
            name=quote(str(name), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | VCenterInventoryResult | None:
    if response.status_code == 200:
        response_200 = VCenterInventoryResult.from_dict(response.json())

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
) -> Response[Error | VCenterInventoryResult]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EvCentersInventoryFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    object_id_filter: str | Unset = UNSET,
    hierarchy_type_filter: EHierarchyType | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: EVmwareInventoryType | Unset = UNSET,
    parent_container_name_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | VCenterInventoryResult]:
    """Get VMware vSphere Server Objects

     The HTTP GET request to the `/api/v1/inventory/vmware/hosts/{name}` path allows you to get an array
    of virtual infrastructure objects of the VMware vSphere server that has the specified
    `name`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore
    Operator, Veeam Tape Operator.</p>

    Args:
        name (str):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EvCentersInventoryFiltersOrderColumn | Unset): Sorts vCenter Servers by one
            of the job parameters.
        order_asc (bool | Unset):
        object_id_filter (str | Unset):
        hierarchy_type_filter (EHierarchyType | Unset): VMware vSphere hierarchy type.
        name_filter (str | Unset):
        type_filter (EVmwareInventoryType | Unset): Type of the VMware vSphere object.<p> Note
            that inventory objects with multiple tags (*Multitag* type) can only be added in the Veeam
            Backup & Replication UI or PowerShell.
        parent_container_name_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | VCenterInventoryResult]
    """

    kwargs = _get_kwargs(
        name=name,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        object_id_filter=object_id_filter,
        hierarchy_type_filter=hierarchy_type_filter,
        name_filter=name_filter,
        type_filter=type_filter,
        parent_container_name_filter=parent_container_name_filter,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EvCentersInventoryFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    object_id_filter: str | Unset = UNSET,
    hierarchy_type_filter: EHierarchyType | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: EVmwareInventoryType | Unset = UNSET,
    parent_container_name_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Error | VCenterInventoryResult | None:
    """Get VMware vSphere Server Objects

     The HTTP GET request to the `/api/v1/inventory/vmware/hosts/{name}` path allows you to get an array
    of virtual infrastructure objects of the VMware vSphere server that has the specified
    `name`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore
    Operator, Veeam Tape Operator.</p>

    Args:
        name (str):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EvCentersInventoryFiltersOrderColumn | Unset): Sorts vCenter Servers by one
            of the job parameters.
        order_asc (bool | Unset):
        object_id_filter (str | Unset):
        hierarchy_type_filter (EHierarchyType | Unset): VMware vSphere hierarchy type.
        name_filter (str | Unset):
        type_filter (EVmwareInventoryType | Unset): Type of the VMware vSphere object.<p> Note
            that inventory objects with multiple tags (*Multitag* type) can only be added in the Veeam
            Backup & Replication UI or PowerShell.
        parent_container_name_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | VCenterInventoryResult
    """

    return sync_detailed(
        name=name,
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        object_id_filter=object_id_filter,
        hierarchy_type_filter=hierarchy_type_filter,
        name_filter=name_filter,
        type_filter=type_filter,
        parent_container_name_filter=parent_container_name_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EvCentersInventoryFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    object_id_filter: str | Unset = UNSET,
    hierarchy_type_filter: EHierarchyType | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: EVmwareInventoryType | Unset = UNSET,
    parent_container_name_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | VCenterInventoryResult]:
    """Get VMware vSphere Server Objects

     The HTTP GET request to the `/api/v1/inventory/vmware/hosts/{name}` path allows you to get an array
    of virtual infrastructure objects of the VMware vSphere server that has the specified
    `name`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore
    Operator, Veeam Tape Operator.</p>

    Args:
        name (str):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EvCentersInventoryFiltersOrderColumn | Unset): Sorts vCenter Servers by one
            of the job parameters.
        order_asc (bool | Unset):
        object_id_filter (str | Unset):
        hierarchy_type_filter (EHierarchyType | Unset): VMware vSphere hierarchy type.
        name_filter (str | Unset):
        type_filter (EVmwareInventoryType | Unset): Type of the VMware vSphere object.<p> Note
            that inventory objects with multiple tags (*Multitag* type) can only be added in the Veeam
            Backup & Replication UI or PowerShell.
        parent_container_name_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | VCenterInventoryResult]
    """

    kwargs = _get_kwargs(
        name=name,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        object_id_filter=object_id_filter,
        hierarchy_type_filter=hierarchy_type_filter,
        name_filter=name_filter,
        type_filter=type_filter,
        parent_container_name_filter=parent_container_name_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EvCentersInventoryFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    object_id_filter: str | Unset = UNSET,
    hierarchy_type_filter: EHierarchyType | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: EVmwareInventoryType | Unset = UNSET,
    parent_container_name_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Error | VCenterInventoryResult | None:
    """Get VMware vSphere Server Objects

     The HTTP GET request to the `/api/v1/inventory/vmware/hosts/{name}` path allows you to get an array
    of virtual infrastructure objects of the VMware vSphere server that has the specified
    `name`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore
    Operator, Veeam Tape Operator.</p>

    Args:
        name (str):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EvCentersInventoryFiltersOrderColumn | Unset): Sorts vCenter Servers by one
            of the job parameters.
        order_asc (bool | Unset):
        object_id_filter (str | Unset):
        hierarchy_type_filter (EHierarchyType | Unset): VMware vSphere hierarchy type.
        name_filter (str | Unset):
        type_filter (EVmwareInventoryType | Unset): Type of the VMware vSphere object.<p> Note
            that inventory objects with multiple tags (*Multitag* type) can only be added in the Veeam
            Backup & Replication UI or PowerShell.
        parent_container_name_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | VCenterInventoryResult
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            object_id_filter=object_id_filter,
            hierarchy_type_filter=hierarchy_type_filter,
            name_filter=name_filter,
            type_filter=type_filter,
            parent_container_name_filter=parent_container_name_filter,
            x_api_version=x_api_version,
        )
    ).parsed

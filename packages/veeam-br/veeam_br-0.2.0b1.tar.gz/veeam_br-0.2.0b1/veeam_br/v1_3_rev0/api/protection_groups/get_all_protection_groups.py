from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_protection_group_filters_order_column import EProtectionGroupFiltersOrderColumn
from ...models.e_protection_group_type import EProtectionGroupType
from ...models.error import Error
from ...models.protection_groups_result import ProtectionGroupsResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EProtectionGroupFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: EProtectionGroupType | Unset = UNSET,
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

    json_type_filter: str | Unset = UNSET
    if not isinstance(type_filter, Unset):
        json_type_filter = type_filter.value

    params["typeFilter"] = json_type_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/agents/protectionGroups",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | ProtectionGroupsResult | None:
    if response.status_code == 200:
        response_200 = ProtectionGroupsResult.from_dict(response.json())

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
) -> Response[Error | ProtectionGroupsResult]:
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
    order_column: EProtectionGroupFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: EProtectionGroupType | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | ProtectionGroupsResult]:
    """Get Protection Groups

     The HTTP GET request to the `/api/v1/agents/protectionGroups` path allows you to get an array of
    protection groups that are added to the physical infrastructure.<p>**Available to**&#58; Veeam
    Backup Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EProtectionGroupFiltersOrderColumn | Unset): Sorts protection groups by one
            of the protection group parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (EProtectionGroupType | Unset): Protection group type
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | ProtectionGroupsResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        type_filter=type_filter,
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
    order_column: EProtectionGroupFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: EProtectionGroupType | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Error | ProtectionGroupsResult | None:
    """Get Protection Groups

     The HTTP GET request to the `/api/v1/agents/protectionGroups` path allows you to get an array of
    protection groups that are added to the physical infrastructure.<p>**Available to**&#58; Veeam
    Backup Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EProtectionGroupFiltersOrderColumn | Unset): Sorts protection groups by one
            of the protection group parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (EProtectionGroupType | Unset): Protection group type
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | ProtectionGroupsResult
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        type_filter=type_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EProtectionGroupFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: EProtectionGroupType | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | ProtectionGroupsResult]:
    """Get Protection Groups

     The HTTP GET request to the `/api/v1/agents/protectionGroups` path allows you to get an array of
    protection groups that are added to the physical infrastructure.<p>**Available to**&#58; Veeam
    Backup Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EProtectionGroupFiltersOrderColumn | Unset): Sorts protection groups by one
            of the protection group parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (EProtectionGroupType | Unset): Protection group type
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | ProtectionGroupsResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        type_filter=type_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EProtectionGroupFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    type_filter: EProtectionGroupType | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Error | ProtectionGroupsResult | None:
    """Get Protection Groups

     The HTTP GET request to the `/api/v1/agents/protectionGroups` path allows you to get an array of
    protection groups that are added to the physical infrastructure.<p>**Available to**&#58; Veeam
    Backup Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EProtectionGroupFiltersOrderColumn | Unset): Sorts protection groups by one
            of the protection group parameters.
        order_asc (bool | Unset):
        name_filter (str | Unset):
        type_filter (EProtectionGroupType | Unset): Protection group type
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | ProtectionGroupsResult
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
            x_api_version=x_api_version,
        )
    ).parsed

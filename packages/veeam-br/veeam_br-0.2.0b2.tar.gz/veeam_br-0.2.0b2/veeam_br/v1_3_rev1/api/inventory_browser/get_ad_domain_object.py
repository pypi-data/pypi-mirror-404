from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.ad_domain_inventory_result import ADDomainInventoryResult
from ...models.ead_domain_filters_order_column import EADDomainFiltersOrderColumn
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: UUID,
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EADDomainFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    full_name_filter: str | Unset = UNSET,
    type_filter: str | Unset = UNSET,
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

    params["fullNameFilter"] = full_name_filter

    params["typeFilter"] = type_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/inventory/activeDirectory/domains/{id}".format(
            id=quote(str(id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ADDomainInventoryResult | Error | None:
    if response.status_code == 200:
        response_200 = ADDomainInventoryResult.from_dict(response.json())

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
) -> Response[ADDomainInventoryResult | Error]:
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
    order_column: EADDomainFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    full_name_filter: str | Unset = UNSET,
    type_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[ADDomainInventoryResult | Error]:
    """Get Active Directory Objects from Domain

     The HTTP GET request to the `/api/v1/inventory/activeDirectory/domains/{id}` endpoint gets an array
    of objects from the Active Directory domain that has the specified `id`. <p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EADDomainFiltersOrderColumn | Unset): Sorts Active Directory domains by one
            of the Active Directory domain parameters.
        order_asc (bool | Unset):
        full_name_filter (str | Unset):
        type_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ADDomainInventoryResult | Error]
    """

    kwargs = _get_kwargs(
        id=id,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        full_name_filter=full_name_filter,
        type_filter=type_filter,
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
    order_column: EADDomainFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    full_name_filter: str | Unset = UNSET,
    type_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> ADDomainInventoryResult | Error | None:
    """Get Active Directory Objects from Domain

     The HTTP GET request to the `/api/v1/inventory/activeDirectory/domains/{id}` endpoint gets an array
    of objects from the Active Directory domain that has the specified `id`. <p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EADDomainFiltersOrderColumn | Unset): Sorts Active Directory domains by one
            of the Active Directory domain parameters.
        order_asc (bool | Unset):
        full_name_filter (str | Unset):
        type_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ADDomainInventoryResult | Error
    """

    return sync_detailed(
        id=id,
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        full_name_filter=full_name_filter,
        type_filter=type_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EADDomainFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    full_name_filter: str | Unset = UNSET,
    type_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[ADDomainInventoryResult | Error]:
    """Get Active Directory Objects from Domain

     The HTTP GET request to the `/api/v1/inventory/activeDirectory/domains/{id}` endpoint gets an array
    of objects from the Active Directory domain that has the specified `id`. <p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EADDomainFiltersOrderColumn | Unset): Sorts Active Directory domains by one
            of the Active Directory domain parameters.
        order_asc (bool | Unset):
        full_name_filter (str | Unset):
        type_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ADDomainInventoryResult | Error]
    """

    kwargs = _get_kwargs(
        id=id,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        full_name_filter=full_name_filter,
        type_filter=type_filter,
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
    order_column: EADDomainFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    full_name_filter: str | Unset = UNSET,
    type_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> ADDomainInventoryResult | Error | None:
    """Get Active Directory Objects from Domain

     The HTTP GET request to the `/api/v1/inventory/activeDirectory/domains/{id}` endpoint gets an array
    of objects from the Active Directory domain that has the specified `id`. <p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EADDomainFiltersOrderColumn | Unset): Sorts Active Directory domains by one
            of the Active Directory domain parameters.
        order_asc (bool | Unset):
        full_name_filter (str | Unset):
        type_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ADDomainInventoryResult | Error
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            full_name_filter=full_name_filter,
            type_filter=type_filter,
            x_api_version=x_api_version,
        )
    ).parsed

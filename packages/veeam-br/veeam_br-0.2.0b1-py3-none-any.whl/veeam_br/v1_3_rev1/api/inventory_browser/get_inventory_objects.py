from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.inventory_browser_filters import InventoryBrowserFilters
from ...models.inventory_browser_result import InventoryBrowserResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    hostname: str,
    *,
    body: InventoryBrowserFilters | Unset = UNSET,
    reset_cache: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    params["resetCache"] = reset_cache

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/inventory/{hostname}".format(
            hostname=quote(str(hostname), safe=""),
        ),
        "params": params,
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | InventoryBrowserResult | None:
    if response.status_code == 200:
        response_200 = InventoryBrowserResult.from_dict(response.json())

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
) -> Response[Error | InventoryBrowserResult]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    hostname: str,
    *,
    client: AuthenticatedClient | Client,
    body: InventoryBrowserFilters | Unset = UNSET,
    reset_cache: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | InventoryBrowserResult]:
    """Get Inventory Objects

     The HTTP POST request to the `/api/v1/inventory/{hostname}` endpoint gets an array of inventory
    objects of a virtualization server (or host) that has the specified `hostname`.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape
    Operator.</p>

    Args:
        hostname (str):
        reset_cache (bool | Unset):
        x_api_version (str):  Default: '1.3-rev1'.
        body (InventoryBrowserFilters | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | InventoryBrowserResult]
    """

    kwargs = _get_kwargs(
        hostname=hostname,
        body=body,
        reset_cache=reset_cache,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    hostname: str,
    *,
    client: AuthenticatedClient | Client,
    body: InventoryBrowserFilters | Unset = UNSET,
    reset_cache: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Error | InventoryBrowserResult | None:
    """Get Inventory Objects

     The HTTP POST request to the `/api/v1/inventory/{hostname}` endpoint gets an array of inventory
    objects of a virtualization server (or host) that has the specified `hostname`.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape
    Operator.</p>

    Args:
        hostname (str):
        reset_cache (bool | Unset):
        x_api_version (str):  Default: '1.3-rev1'.
        body (InventoryBrowserFilters | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | InventoryBrowserResult
    """

    return sync_detailed(
        hostname=hostname,
        client=client,
        body=body,
        reset_cache=reset_cache,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    hostname: str,
    *,
    client: AuthenticatedClient | Client,
    body: InventoryBrowserFilters | Unset = UNSET,
    reset_cache: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | InventoryBrowserResult]:
    """Get Inventory Objects

     The HTTP POST request to the `/api/v1/inventory/{hostname}` endpoint gets an array of inventory
    objects of a virtualization server (or host) that has the specified `hostname`.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape
    Operator.</p>

    Args:
        hostname (str):
        reset_cache (bool | Unset):
        x_api_version (str):  Default: '1.3-rev1'.
        body (InventoryBrowserFilters | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | InventoryBrowserResult]
    """

    kwargs = _get_kwargs(
        hostname=hostname,
        body=body,
        reset_cache=reset_cache,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    hostname: str,
    *,
    client: AuthenticatedClient | Client,
    body: InventoryBrowserFilters | Unset = UNSET,
    reset_cache: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Error | InventoryBrowserResult | None:
    """Get Inventory Objects

     The HTTP POST request to the `/api/v1/inventory/{hostname}` endpoint gets an array of inventory
    objects of a virtualization server (or host) that has the specified `hostname`.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape
    Operator.</p>

    Args:
        hostname (str):
        reset_cache (bool | Unset):
        x_api_version (str):  Default: '1.3-rev1'.
        body (InventoryBrowserFilters | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | InventoryBrowserResult
    """

    return (
        await asyncio_detailed(
            hostname=hostname,
            client=client,
            body=body,
            reset_cache=reset_cache,
            x_api_version=x_api_version,
        )
    ).parsed

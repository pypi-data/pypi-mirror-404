from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.inventory_browser_filters import InventoryBrowserFilters
from ...models.inventory_browser_result import InventoryBrowserResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: InventoryBrowserFilters | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/inventory",
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
    *,
    client: AuthenticatedClient | Client,
    body: InventoryBrowserFilters | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | InventoryBrowserResult]:
    r"""Get All Servers

     The HTTP POST request to the `/api/v1/inventory` path allows you to get an array of all servers and
    hosts added to the backup infrastructure.<div class=\"tip\"><strong>TIP</strong> <br>To filter
    servers by type, use the following possible values&#58; *VCenterServer*, *Folder*, *Host*,
    *CloudDirectorServer*. For details, see request samples.</div><p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (InventoryBrowserFilters | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | InventoryBrowserResult]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: InventoryBrowserFilters | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Error | InventoryBrowserResult | None:
    r"""Get All Servers

     The HTTP POST request to the `/api/v1/inventory` path allows you to get an array of all servers and
    hosts added to the backup infrastructure.<div class=\"tip\"><strong>TIP</strong> <br>To filter
    servers by type, use the following possible values&#58; *VCenterServer*, *Folder*, *Host*,
    *CloudDirectorServer*. For details, see request samples.</div><p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (InventoryBrowserFilters | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | InventoryBrowserResult
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: InventoryBrowserFilters | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | InventoryBrowserResult]:
    r"""Get All Servers

     The HTTP POST request to the `/api/v1/inventory` path allows you to get an array of all servers and
    hosts added to the backup infrastructure.<div class=\"tip\"><strong>TIP</strong> <br>To filter
    servers by type, use the following possible values&#58; *VCenterServer*, *Folder*, *Host*,
    *CloudDirectorServer*. For details, see request samples.</div><p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (InventoryBrowserFilters | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | InventoryBrowserResult]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: InventoryBrowserFilters | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Error | InventoryBrowserResult | None:
    r"""Get All Servers

     The HTTP POST request to the `/api/v1/inventory` path allows you to get an array of all servers and
    hosts added to the backup infrastructure.<div class=\"tip\"><strong>TIP</strong> <br>To filter
    servers by type, use the following possible values&#58; *VCenterServer*, *Folder*, *Host*,
    *CloudDirectorServer*. For details, see request samples.</div><p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (InventoryBrowserFilters | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | InventoryBrowserResult
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

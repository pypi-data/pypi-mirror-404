from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.task_model import TaskModel
from ...types import Response


def _get_kwargs(
    hostname: str,
    *,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/inventory/{hostname}/rescan".format(
            hostname=quote(str(hostname), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Error | TaskModel | None:
    if response.status_code == 201:
        response_201 = TaskModel.from_dict(response.json())

        return response_201

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Error | TaskModel]:
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
    x_api_version: str = "1.3-rev1",
) -> Response[Error | TaskModel]:
    """Rescan Inventory Objects

     The HTTP POST request to the `/api/v1/inventory/{hostname}/rescan` endpoint rescans inventory
    objects of a virtualization server (or host) that has the specified `hostname`.<p>**Available
    to**&#58; Veeam Backup Administrator.</p>

    Args:
        hostname (str):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | TaskModel]
    """

    kwargs = _get_kwargs(
        hostname=hostname,
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
    x_api_version: str = "1.3-rev1",
) -> Error | TaskModel | None:
    """Rescan Inventory Objects

     The HTTP POST request to the `/api/v1/inventory/{hostname}/rescan` endpoint rescans inventory
    objects of a virtualization server (or host) that has the specified `hostname`.<p>**Available
    to**&#58; Veeam Backup Administrator.</p>

    Args:
        hostname (str):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | TaskModel
    """

    return sync_detailed(
        hostname=hostname,
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    hostname: str,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | TaskModel]:
    """Rescan Inventory Objects

     The HTTP POST request to the `/api/v1/inventory/{hostname}/rescan` endpoint rescans inventory
    objects of a virtualization server (or host) that has the specified `hostname`.<p>**Available
    to**&#58; Veeam Backup Administrator.</p>

    Args:
        hostname (str):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | TaskModel]
    """

    kwargs = _get_kwargs(
        hostname=hostname,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    hostname: str,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev1",
) -> Error | TaskModel | None:
    """Rescan Inventory Objects

     The HTTP POST request to the `/api/v1/inventory/{hostname}/rescan` endpoint rescans inventory
    objects of a virtualization server (or host) that has the specified `hostname`.<p>**Available
    to**&#58; Veeam Backup Administrator.</p>

    Args:
        hostname (str):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | TaskModel
    """

    return (
        await asyncio_detailed(
            hostname=hostname,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed

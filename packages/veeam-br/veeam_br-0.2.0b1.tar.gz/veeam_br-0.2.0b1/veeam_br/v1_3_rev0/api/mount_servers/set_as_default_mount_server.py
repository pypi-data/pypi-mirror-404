from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.mount_server_model import MountServerModel
from ...types import Response


def _get_kwargs(
    id: UUID,
    *,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backupInfrastructure/mountServers/{id}/default".format(
            id=quote(str(id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | MountServerModel | None:
    if response.status_code == 201:
        response_201 = MountServerModel.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

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
) -> Response[Error | MountServerModel]:
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
    x_api_version: str = "1.3-rev0",
) -> Response[Error | MountServerModel]:
    """Set Default Mount Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/mountServers/{id}/default` path allows
    you to set a default mount server. After you set a default mount server, new repositories will be
    assigned this mount server by default, for targets with the same OS as the mount server.<p>For
    example, if you specify a Windows machine as a default mount server, all new repositories will use
    this mount server as the default mount server for advanced recovery operations to Windows
    machines.</p> <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | MountServerModel]
    """

    kwargs = _get_kwargs(
        id=id,
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
    x_api_version: str = "1.3-rev0",
) -> Error | MountServerModel | None:
    """Set Default Mount Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/mountServers/{id}/default` path allows
    you to set a default mount server. After you set a default mount server, new repositories will be
    assigned this mount server by default, for targets with the same OS as the mount server.<p>For
    example, if you specify a Windows machine as a default mount server, all new repositories will use
    this mount server as the default mount server for advanced recovery operations to Windows
    machines.</p> <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | MountServerModel
    """

    return sync_detailed(
        id=id,
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | MountServerModel]:
    """Set Default Mount Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/mountServers/{id}/default` path allows
    you to set a default mount server. After you set a default mount server, new repositories will be
    assigned this mount server by default, for targets with the same OS as the mount server.<p>For
    example, if you specify a Windows machine as a default mount server, all new repositories will use
    this mount server as the default mount server for advanced recovery operations to Windows
    machines.</p> <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | MountServerModel]
    """

    kwargs = _get_kwargs(
        id=id,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev0",
) -> Error | MountServerModel | None:
    """Set Default Mount Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/mountServers/{id}/default` path allows
    you to set a default mount server. After you set a default mount server, new repositories will be
    assigned this mount server by default, for targets with the same OS as the mount server.<p>For
    example, if you specify a Windows machine as a default mount server, all new repositories will use
    this mount server as the default mount server for advanced recovery operations to Windows
    machines.</p> <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | MountServerModel
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed

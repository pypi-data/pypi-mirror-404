from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.socket_license_workload_model import SocketLicenseWorkloadModel
from ...types import Response


def _get_kwargs(
    host_id: UUID,
    *,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/license/sockets/{host_id}/revoke".format(
            host_id=quote(str(host_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | SocketLicenseWorkloadModel | None:
    if response.status_code == 200:
        response_200 = SocketLicenseWorkloadModel.from_dict(response.json())

        return response_200

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
) -> Response[Error | SocketLicenseWorkloadModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    host_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | SocketLicenseWorkloadModel]:
    """Revoke Socket License

     The HTTP POST request to the `/api/v1/license/sockets/{hostId}/revoke` path allows you to revoke a
    socket license from the host with the specified `hostId`.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        host_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | SocketLicenseWorkloadModel]
    """

    kwargs = _get_kwargs(
        host_id=host_id,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    host_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev0",
) -> Error | SocketLicenseWorkloadModel | None:
    """Revoke Socket License

     The HTTP POST request to the `/api/v1/license/sockets/{hostId}/revoke` path allows you to revoke a
    socket license from the host with the specified `hostId`.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        host_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | SocketLicenseWorkloadModel
    """

    return sync_detailed(
        host_id=host_id,
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    host_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | SocketLicenseWorkloadModel]:
    """Revoke Socket License

     The HTTP POST request to the `/api/v1/license/sockets/{hostId}/revoke` path allows you to revoke a
    socket license from the host with the specified `hostId`.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        host_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | SocketLicenseWorkloadModel]
    """

    kwargs = _get_kwargs(
        host_id=host_id,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    host_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev0",
) -> Error | SocketLicenseWorkloadModel | None:
    """Revoke Socket License

     The HTTP POST request to the `/api/v1/license/sockets/{hostId}/revoke` path allows you to revoke a
    socket license from the host with the specified `hostId`.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        host_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | SocketLicenseWorkloadModel
    """

    return (
        await asyncio_detailed(
            host_id=host_id,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed

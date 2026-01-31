from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.cloud_director_host_discovery_result import CloudDirectorHostDiscoveryResult
from ...models.cloud_director_host_discovery_spec import CloudDirectorHostDiscoverySpec
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    *,
    body: CloudDirectorHostDiscoverySpec,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backupInfrastructure/managedServers/cloudDirectorHosts",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CloudDirectorHostDiscoveryResult | Error | None:
    if response.status_code == 200:
        response_200 = CloudDirectorHostDiscoveryResult.from_dict(response.json())

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
) -> Response[CloudDirectorHostDiscoveryResult | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CloudDirectorHostDiscoverySpec,
    x_api_version: str = "1.2-rev1",
) -> Response[CloudDirectorHostDiscoveryResult | Error]:
    """Get vCenter Servers Attached to Cloud Director Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/managedServers/cloudDirectorHosts` path
    allows you to get an array of vCenter Servers attached to a specific VMware Cloud Director
    server.<p> **Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (CloudDirectorHostDiscoverySpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CloudDirectorHostDiscoveryResult | Error]
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
    body: CloudDirectorHostDiscoverySpec,
    x_api_version: str = "1.2-rev1",
) -> CloudDirectorHostDiscoveryResult | Error | None:
    """Get vCenter Servers Attached to Cloud Director Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/managedServers/cloudDirectorHosts` path
    allows you to get an array of vCenter Servers attached to a specific VMware Cloud Director
    server.<p> **Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (CloudDirectorHostDiscoverySpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CloudDirectorHostDiscoveryResult | Error
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CloudDirectorHostDiscoverySpec,
    x_api_version: str = "1.2-rev1",
) -> Response[CloudDirectorHostDiscoveryResult | Error]:
    """Get vCenter Servers Attached to Cloud Director Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/managedServers/cloudDirectorHosts` path
    allows you to get an array of vCenter Servers attached to a specific VMware Cloud Director
    server.<p> **Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (CloudDirectorHostDiscoverySpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CloudDirectorHostDiscoveryResult | Error]
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
    body: CloudDirectorHostDiscoverySpec,
    x_api_version: str = "1.2-rev1",
) -> CloudDirectorHostDiscoveryResult | Error | None:
    """Get vCenter Servers Attached to Cloud Director Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/managedServers/cloudDirectorHosts` path
    allows you to get an array of vCenter Servers attached to a specific VMware Cloud Director
    server.<p> **Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (CloudDirectorHostDiscoverySpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CloudDirectorHostDiscoveryResult | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

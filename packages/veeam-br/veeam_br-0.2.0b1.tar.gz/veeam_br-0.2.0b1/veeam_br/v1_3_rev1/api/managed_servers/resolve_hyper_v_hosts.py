from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.hv_host_discovery_result import HvHostDiscoveryResult
from ...models.hv_host_discovery_spec import HvHostDiscoverySpec
from ...types import Response


def _get_kwargs(
    *,
    body: HvHostDiscoverySpec,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backupInfrastructure/managedServers/hyperVHosts",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | HvHostDiscoveryResult | None:
    if response.status_code == 200:
        response_200 = HvHostDiscoveryResult.from_dict(response.json())

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
) -> Response[Error | HvHostDiscoveryResult]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: HvHostDiscoverySpec,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | HvHostDiscoveryResult]:
    """Get Microsoft Hyper-V Servers Managed by Microsoft Hyper-V Cluster or SCVMM Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/managedServers/hyperVHosts` endpoint gets
    an array of Microsoft Hyper-V Servers managed by a specific Microsoft Hyper-V cluster or an SCVMM
    server. <p>Before you discover the hosts of your SCVMM server, you must add the SCVMM server to the
    Veeam Backup & Replication infrastructure.</p><p> **Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (HvHostDiscoverySpec): Settings for Microsoft Hyper-V hosts discovery.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | HvHostDiscoveryResult]
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
    body: HvHostDiscoverySpec,
    x_api_version: str = "1.3-rev1",
) -> Error | HvHostDiscoveryResult | None:
    """Get Microsoft Hyper-V Servers Managed by Microsoft Hyper-V Cluster or SCVMM Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/managedServers/hyperVHosts` endpoint gets
    an array of Microsoft Hyper-V Servers managed by a specific Microsoft Hyper-V cluster or an SCVMM
    server. <p>Before you discover the hosts of your SCVMM server, you must add the SCVMM server to the
    Veeam Backup & Replication infrastructure.</p><p> **Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (HvHostDiscoverySpec): Settings for Microsoft Hyper-V hosts discovery.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | HvHostDiscoveryResult
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: HvHostDiscoverySpec,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | HvHostDiscoveryResult]:
    """Get Microsoft Hyper-V Servers Managed by Microsoft Hyper-V Cluster or SCVMM Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/managedServers/hyperVHosts` endpoint gets
    an array of Microsoft Hyper-V Servers managed by a specific Microsoft Hyper-V cluster or an SCVMM
    server. <p>Before you discover the hosts of your SCVMM server, you must add the SCVMM server to the
    Veeam Backup & Replication infrastructure.</p><p> **Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (HvHostDiscoverySpec): Settings for Microsoft Hyper-V hosts discovery.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | HvHostDiscoveryResult]
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
    body: HvHostDiscoverySpec,
    x_api_version: str = "1.3-rev1",
) -> Error | HvHostDiscoveryResult | None:
    """Get Microsoft Hyper-V Servers Managed by Microsoft Hyper-V Cluster or SCVMM Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/managedServers/hyperVHosts` endpoint gets
    an array of Microsoft Hyper-V Servers managed by a specific Microsoft Hyper-V cluster or an SCVMM
    server. <p>Before you discover the hosts of your SCVMM server, you must add the SCVMM server to the
    Veeam Backup & Replication infrastructure.</p><p> **Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (HvHostDiscoverySpec): Settings for Microsoft Hyper-V hosts discovery.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | HvHostDiscoveryResult
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

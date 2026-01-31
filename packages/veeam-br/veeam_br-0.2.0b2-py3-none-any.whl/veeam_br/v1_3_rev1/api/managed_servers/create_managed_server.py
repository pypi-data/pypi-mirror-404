from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.managed_server_spec import ManagedServerSpec
from ...models.session_model import SessionModel
from ...types import Response


def _get_kwargs(
    *,
    body: ManagedServerSpec,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backupInfrastructure/managedServers",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Error | SessionModel | None:
    if response.status_code == 201:
        response_201 = SessionModel.from_dict(response.json())

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
) -> Response[Error | SessionModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ManagedServerSpec,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | SessionModel]:
    """Add Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/managedServers` endpoint adds a server to
    the backup infrastructure. <p>If you want to add a Microsoft Hyper-V cluster and include only
    specific Microsoft Hyper-V hosts, follow these steps&#58;</p> <ol><li>Add the credentials used to
    connect to the Microsoft Hyper-V cluster&#58; [Add Credentials
    Record](Credentials#operation/CreateCreds). You will need to specify the credentials ID in the
    following requests.</li> <li>Discover the hosts managed by the cluster&#58; [Get Microsoft Hyper-V
    Servers Managed by Microsoft Hyper-V Cluster or SCVMM Server](Managed-
    Servers#operation/ResolveHyperVHosts).</li> <li>Add the Microsoft Hyper-V cluster using this
    request. In the request body, specify the necessary hosts.</li></ol> <p>If you want to add an SCVMM
    server and include only specific Microsoft Hyper-V hosts, follow these steps&#58;</p> <ol><li>Add
    the credentials used to connect to the SCVMM server&#58; [Add Credentials
    Record](Credentials#operation/CreateCreds). You will need to specify the credentials ID in the
    following requests.</li> <li>To add an SCVMM server without hosts, use this request and set
    `addAllServers` to `false` in the request body .</li> <li>Discover the hosts managed by the SCVMM
    server&#58; [Get Microsoft Hyper-V Servers Managed by Microsoft Hyper-V Cluster or SCVMM
    Server](Managed-Servers#operation/ResolveHyperVHosts).</li> <li>To add the necessary hosts, edit the
    SCVMM server&#58; [Edit Server](Managed-Servers#operation/UpdateManagedServer).</li> </ol>
    <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (ManagedServerSpec): Managed server settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | SessionModel]
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
    body: ManagedServerSpec,
    x_api_version: str = "1.3-rev1",
) -> Error | SessionModel | None:
    """Add Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/managedServers` endpoint adds a server to
    the backup infrastructure. <p>If you want to add a Microsoft Hyper-V cluster and include only
    specific Microsoft Hyper-V hosts, follow these steps&#58;</p> <ol><li>Add the credentials used to
    connect to the Microsoft Hyper-V cluster&#58; [Add Credentials
    Record](Credentials#operation/CreateCreds). You will need to specify the credentials ID in the
    following requests.</li> <li>Discover the hosts managed by the cluster&#58; [Get Microsoft Hyper-V
    Servers Managed by Microsoft Hyper-V Cluster or SCVMM Server](Managed-
    Servers#operation/ResolveHyperVHosts).</li> <li>Add the Microsoft Hyper-V cluster using this
    request. In the request body, specify the necessary hosts.</li></ol> <p>If you want to add an SCVMM
    server and include only specific Microsoft Hyper-V hosts, follow these steps&#58;</p> <ol><li>Add
    the credentials used to connect to the SCVMM server&#58; [Add Credentials
    Record](Credentials#operation/CreateCreds). You will need to specify the credentials ID in the
    following requests.</li> <li>To add an SCVMM server without hosts, use this request and set
    `addAllServers` to `false` in the request body .</li> <li>Discover the hosts managed by the SCVMM
    server&#58; [Get Microsoft Hyper-V Servers Managed by Microsoft Hyper-V Cluster or SCVMM
    Server](Managed-Servers#operation/ResolveHyperVHosts).</li> <li>To add the necessary hosts, edit the
    SCVMM server&#58; [Edit Server](Managed-Servers#operation/UpdateManagedServer).</li> </ol>
    <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (ManagedServerSpec): Managed server settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | SessionModel
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ManagedServerSpec,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | SessionModel]:
    """Add Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/managedServers` endpoint adds a server to
    the backup infrastructure. <p>If you want to add a Microsoft Hyper-V cluster and include only
    specific Microsoft Hyper-V hosts, follow these steps&#58;</p> <ol><li>Add the credentials used to
    connect to the Microsoft Hyper-V cluster&#58; [Add Credentials
    Record](Credentials#operation/CreateCreds). You will need to specify the credentials ID in the
    following requests.</li> <li>Discover the hosts managed by the cluster&#58; [Get Microsoft Hyper-V
    Servers Managed by Microsoft Hyper-V Cluster or SCVMM Server](Managed-
    Servers#operation/ResolveHyperVHosts).</li> <li>Add the Microsoft Hyper-V cluster using this
    request. In the request body, specify the necessary hosts.</li></ol> <p>If you want to add an SCVMM
    server and include only specific Microsoft Hyper-V hosts, follow these steps&#58;</p> <ol><li>Add
    the credentials used to connect to the SCVMM server&#58; [Add Credentials
    Record](Credentials#operation/CreateCreds). You will need to specify the credentials ID in the
    following requests.</li> <li>To add an SCVMM server without hosts, use this request and set
    `addAllServers` to `false` in the request body .</li> <li>Discover the hosts managed by the SCVMM
    server&#58; [Get Microsoft Hyper-V Servers Managed by Microsoft Hyper-V Cluster or SCVMM
    Server](Managed-Servers#operation/ResolveHyperVHosts).</li> <li>To add the necessary hosts, edit the
    SCVMM server&#58; [Edit Server](Managed-Servers#operation/UpdateManagedServer).</li> </ol>
    <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (ManagedServerSpec): Managed server settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | SessionModel]
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
    body: ManagedServerSpec,
    x_api_version: str = "1.3-rev1",
) -> Error | SessionModel | None:
    """Add Server

     The HTTP POST request to the `/api/v1/backupInfrastructure/managedServers` endpoint adds a server to
    the backup infrastructure. <p>If you want to add a Microsoft Hyper-V cluster and include only
    specific Microsoft Hyper-V hosts, follow these steps&#58;</p> <ol><li>Add the credentials used to
    connect to the Microsoft Hyper-V cluster&#58; [Add Credentials
    Record](Credentials#operation/CreateCreds). You will need to specify the credentials ID in the
    following requests.</li> <li>Discover the hosts managed by the cluster&#58; [Get Microsoft Hyper-V
    Servers Managed by Microsoft Hyper-V Cluster or SCVMM Server](Managed-
    Servers#operation/ResolveHyperVHosts).</li> <li>Add the Microsoft Hyper-V cluster using this
    request. In the request body, specify the necessary hosts.</li></ol> <p>If you want to add an SCVMM
    server and include only specific Microsoft Hyper-V hosts, follow these steps&#58;</p> <ol><li>Add
    the credentials used to connect to the SCVMM server&#58; [Add Credentials
    Record](Credentials#operation/CreateCreds). You will need to specify the credentials ID in the
    following requests.</li> <li>To add an SCVMM server without hosts, use this request and set
    `addAllServers` to `false` in the request body .</li> <li>Discover the hosts managed by the SCVMM
    server&#58; [Get Microsoft Hyper-V Servers Managed by Microsoft Hyper-V Cluster or SCVMM
    Server](Managed-Servers#operation/ResolveHyperVHosts).</li> <li>To add the necessary hosts, edit the
    SCVMM server&#58; [Edit Server](Managed-Servers#operation/UpdateManagedServer).</li> </ol>
    <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (ManagedServerSpec): Managed server settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | SessionModel
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

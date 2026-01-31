from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.azure_instant_vm_recovery_mount import AzureInstantVMRecoveryMount
from ...models.azure_instant_vm_recovery_spec import AzureInstantVMRecoverySpec
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    *,
    body: AzureInstantVMRecoverySpec,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/restore/instantRecovery/azure/vm",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AzureInstantVMRecoveryMount | Error | None:
    if response.status_code == 201:
        response_201 = AzureInstantVMRecoveryMount.from_dict(response.json())

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
) -> Response[AzureInstantVMRecoveryMount | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AzureInstantVMRecoverySpec,
    x_api_version: str = "1.3-rev1",
) -> Response[AzureInstantVMRecoveryMount | Error]:
    r"""Start Instant Recovery to Microsoft Azure

     The HTTP POST request to the `/api/v1/restore/instantRecovery/azure/vm` endpoint starts Instant
    Recovery of a Linux or Microsoft Windows machine to Microsoft Azure. <div
    class=\"note\"><strong>NOTE</strong><br> Deploying a helper appliance template with REST API is not
    supported in this version. Before you run this request, you must deploy a helper appliance template
    in the Veeam Backup & Replication UI or with the `Deploy-VBRAzureApplianceTemplate` cmdlet.</div>
    <p> To get the values required in the request body, run the following requests:<ol> <li> Run the
    [Get All Restore Points](Restore-Points#operation/GetAllObjectRestorePoints) request to get the
    `RestorePointId` property value.</li> <li> Run the [Get Restore Point Disks](Restore-
    Points#operation/GetObjectRestorePointDisksWithFiltering) request to get the `diskUid` property
    value.</li> <li> Run the [Get All Cloud Credentials](Credentials#operation/GetAllCloudCreds) request
    to get the `subscriptionId` property value. Use the ID that Veeam Backup & Replication assigned to
    the Microsoft Azure subscription. You can find this ID in the
    `data[x].subscription.subscriptions[y].id` property, where `x` and `y` are the ordinal numbers of
    the objects in the arrays.</li> <li> Run the [Get Cloud Hierarchy](Cloud-
    Browser#operation/BrowseCloudEntity) request to get the values for the remaining required
    properties.</li></ol> <p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (AzureInstantVMRecoverySpec): Settings for Instant Recovery to Microsoft Azure.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AzureInstantVMRecoveryMount | Error]
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
    body: AzureInstantVMRecoverySpec,
    x_api_version: str = "1.3-rev1",
) -> AzureInstantVMRecoveryMount | Error | None:
    r"""Start Instant Recovery to Microsoft Azure

     The HTTP POST request to the `/api/v1/restore/instantRecovery/azure/vm` endpoint starts Instant
    Recovery of a Linux or Microsoft Windows machine to Microsoft Azure. <div
    class=\"note\"><strong>NOTE</strong><br> Deploying a helper appliance template with REST API is not
    supported in this version. Before you run this request, you must deploy a helper appliance template
    in the Veeam Backup & Replication UI or with the `Deploy-VBRAzureApplianceTemplate` cmdlet.</div>
    <p> To get the values required in the request body, run the following requests:<ol> <li> Run the
    [Get All Restore Points](Restore-Points#operation/GetAllObjectRestorePoints) request to get the
    `RestorePointId` property value.</li> <li> Run the [Get Restore Point Disks](Restore-
    Points#operation/GetObjectRestorePointDisksWithFiltering) request to get the `diskUid` property
    value.</li> <li> Run the [Get All Cloud Credentials](Credentials#operation/GetAllCloudCreds) request
    to get the `subscriptionId` property value. Use the ID that Veeam Backup & Replication assigned to
    the Microsoft Azure subscription. You can find this ID in the
    `data[x].subscription.subscriptions[y].id` property, where `x` and `y` are the ordinal numbers of
    the objects in the arrays.</li> <li> Run the [Get Cloud Hierarchy](Cloud-
    Browser#operation/BrowseCloudEntity) request to get the values for the remaining required
    properties.</li></ol> <p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (AzureInstantVMRecoverySpec): Settings for Instant Recovery to Microsoft Azure.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AzureInstantVMRecoveryMount | Error
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AzureInstantVMRecoverySpec,
    x_api_version: str = "1.3-rev1",
) -> Response[AzureInstantVMRecoveryMount | Error]:
    r"""Start Instant Recovery to Microsoft Azure

     The HTTP POST request to the `/api/v1/restore/instantRecovery/azure/vm` endpoint starts Instant
    Recovery of a Linux or Microsoft Windows machine to Microsoft Azure. <div
    class=\"note\"><strong>NOTE</strong><br> Deploying a helper appliance template with REST API is not
    supported in this version. Before you run this request, you must deploy a helper appliance template
    in the Veeam Backup & Replication UI or with the `Deploy-VBRAzureApplianceTemplate` cmdlet.</div>
    <p> To get the values required in the request body, run the following requests:<ol> <li> Run the
    [Get All Restore Points](Restore-Points#operation/GetAllObjectRestorePoints) request to get the
    `RestorePointId` property value.</li> <li> Run the [Get Restore Point Disks](Restore-
    Points#operation/GetObjectRestorePointDisksWithFiltering) request to get the `diskUid` property
    value.</li> <li> Run the [Get All Cloud Credentials](Credentials#operation/GetAllCloudCreds) request
    to get the `subscriptionId` property value. Use the ID that Veeam Backup & Replication assigned to
    the Microsoft Azure subscription. You can find this ID in the
    `data[x].subscription.subscriptions[y].id` property, where `x` and `y` are the ordinal numbers of
    the objects in the arrays.</li> <li> Run the [Get Cloud Hierarchy](Cloud-
    Browser#operation/BrowseCloudEntity) request to get the values for the remaining required
    properties.</li></ol> <p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (AzureInstantVMRecoverySpec): Settings for Instant Recovery to Microsoft Azure.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AzureInstantVMRecoveryMount | Error]
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
    body: AzureInstantVMRecoverySpec,
    x_api_version: str = "1.3-rev1",
) -> AzureInstantVMRecoveryMount | Error | None:
    r"""Start Instant Recovery to Microsoft Azure

     The HTTP POST request to the `/api/v1/restore/instantRecovery/azure/vm` endpoint starts Instant
    Recovery of a Linux or Microsoft Windows machine to Microsoft Azure. <div
    class=\"note\"><strong>NOTE</strong><br> Deploying a helper appliance template with REST API is not
    supported in this version. Before you run this request, you must deploy a helper appliance template
    in the Veeam Backup & Replication UI or with the `Deploy-VBRAzureApplianceTemplate` cmdlet.</div>
    <p> To get the values required in the request body, run the following requests:<ol> <li> Run the
    [Get All Restore Points](Restore-Points#operation/GetAllObjectRestorePoints) request to get the
    `RestorePointId` property value.</li> <li> Run the [Get Restore Point Disks](Restore-
    Points#operation/GetObjectRestorePointDisksWithFiltering) request to get the `diskUid` property
    value.</li> <li> Run the [Get All Cloud Credentials](Credentials#operation/GetAllCloudCreds) request
    to get the `subscriptionId` property value. Use the ID that Veeam Backup & Replication assigned to
    the Microsoft Azure subscription. You can find this ID in the
    `data[x].subscription.subscriptions[y].id` property, where `x` and `y` are the ordinal numbers of
    the objects in the arrays.</li> <li> Run the [Get Cloud Hierarchy](Cloud-
    Browser#operation/BrowseCloudEntity) request to get the values for the remaining required
    properties.</li></ol> <p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (AzureInstantVMRecoverySpec): Settings for Instant Recovery to Microsoft Azure.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AzureInstantVMRecoveryMount | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.session_model import SessionModel
from ...models.vmware_fcd_instant_recovery_spec import VmwareFcdInstantRecoverySpec
from ...types import Response


def _get_kwargs(
    *,
    body: VmwareFcdInstantRecoverySpec,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/restore/instantRecovery/vSphere/fcd",
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
    body: VmwareFcdInstantRecoverySpec,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | SessionModel]:
    """Start Instant FCD Recovery

     The HTTP POST request to the `/api/v1/restore/instantRecovery/vSphere/fcd` path allows you to start
    Instant FCD Recovery from the restore point to the destination cluster.<p>Specify the destination
    cluster in the `destinationCluster` parameter of the request body as a model of the VMware vSphere
    object. For details on how to get the cluster model, see [Get Inventory Objects](#tag/Inventory-
    Browser/operation/GetInventoryObjects).<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Restore Operator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (VmwareFcdInstantRecoverySpec): Instant FCD Recovery configuration:<ul> <li>Restore
            point ID</li> <li>Destination cluster</li> <li>Disks for restore</li> <li>Write
            cache</li></ul>

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
    body: VmwareFcdInstantRecoverySpec,
    x_api_version: str = "1.2-rev1",
) -> Error | SessionModel | None:
    """Start Instant FCD Recovery

     The HTTP POST request to the `/api/v1/restore/instantRecovery/vSphere/fcd` path allows you to start
    Instant FCD Recovery from the restore point to the destination cluster.<p>Specify the destination
    cluster in the `destinationCluster` parameter of the request body as a model of the VMware vSphere
    object. For details on how to get the cluster model, see [Get Inventory Objects](#tag/Inventory-
    Browser/operation/GetInventoryObjects).<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Restore Operator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (VmwareFcdInstantRecoverySpec): Instant FCD Recovery configuration:<ul> <li>Restore
            point ID</li> <li>Destination cluster</li> <li>Disks for restore</li> <li>Write
            cache</li></ul>

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
    body: VmwareFcdInstantRecoverySpec,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | SessionModel]:
    """Start Instant FCD Recovery

     The HTTP POST request to the `/api/v1/restore/instantRecovery/vSphere/fcd` path allows you to start
    Instant FCD Recovery from the restore point to the destination cluster.<p>Specify the destination
    cluster in the `destinationCluster` parameter of the request body as a model of the VMware vSphere
    object. For details on how to get the cluster model, see [Get Inventory Objects](#tag/Inventory-
    Browser/operation/GetInventoryObjects).<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Restore Operator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (VmwareFcdInstantRecoverySpec): Instant FCD Recovery configuration:<ul> <li>Restore
            point ID</li> <li>Destination cluster</li> <li>Disks for restore</li> <li>Write
            cache</li></ul>

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
    body: VmwareFcdInstantRecoverySpec,
    x_api_version: str = "1.2-rev1",
) -> Error | SessionModel | None:
    """Start Instant FCD Recovery

     The HTTP POST request to the `/api/v1/restore/instantRecovery/vSphere/fcd` path allows you to start
    Instant FCD Recovery from the restore point to the destination cluster.<p>Specify the destination
    cluster in the `destinationCluster` parameter of the request body as a model of the VMware vSphere
    object. For details on how to get the cluster model, see [Get Inventory Objects](#tag/Inventory-
    Browser/operation/GetInventoryObjects).<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Restore Operator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (VmwareFcdInstantRecoverySpec): Instant FCD Recovery configuration:<ul> <li>Restore
            point ID</li> <li>Destination cluster</li> <li>Disks for restore</li> <li>Write
            cache</li></ul>

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

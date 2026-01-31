from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.vmware_fcd_instant_recovery_mount import VmwareFcdInstantRecoveryMount
from ...types import Response


def _get_kwargs(
    mount_id: UUID,
    *,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/restore/instantRecovery/vSphere/fcd/{mount_id}".format(
            mount_id=quote(str(mount_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | VmwareFcdInstantRecoveryMount | None:
    if response.status_code == 200:
        response_200 = VmwareFcdInstantRecoveryMount.from_dict(response.json())

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
) -> Response[Error | VmwareFcdInstantRecoveryMount]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    mount_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | VmwareFcdInstantRecoveryMount]:
    """Get FCD Mount Point

     The HTTP GET request to the `/api/v1/restore/instantRecovery/vSphere/fcd/{mountId}` path allows you
    to get information about the mounted vPower NFS datastore, such as restore session ID, mount point
    state, instant FCD recovery settings and disks that will be recovered.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam
    Backup Viewer.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | VmwareFcdInstantRecoveryMount]
    """

    kwargs = _get_kwargs(
        mount_id=mount_id,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    mount_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.2-rev1",
) -> Error | VmwareFcdInstantRecoveryMount | None:
    """Get FCD Mount Point

     The HTTP GET request to the `/api/v1/restore/instantRecovery/vSphere/fcd/{mountId}` path allows you
    to get information about the mounted vPower NFS datastore, such as restore session ID, mount point
    state, instant FCD recovery settings and disks that will be recovered.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam
    Backup Viewer.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | VmwareFcdInstantRecoveryMount
    """

    return sync_detailed(
        mount_id=mount_id,
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    mount_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | VmwareFcdInstantRecoveryMount]:
    """Get FCD Mount Point

     The HTTP GET request to the `/api/v1/restore/instantRecovery/vSphere/fcd/{mountId}` path allows you
    to get information about the mounted vPower NFS datastore, such as restore session ID, mount point
    state, instant FCD recovery settings and disks that will be recovered.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam
    Backup Viewer.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | VmwareFcdInstantRecoveryMount]
    """

    kwargs = _get_kwargs(
        mount_id=mount_id,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    mount_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.2-rev1",
) -> Error | VmwareFcdInstantRecoveryMount | None:
    """Get FCD Mount Point

     The HTTP GET request to the `/api/v1/restore/instantRecovery/vSphere/fcd/{mountId}` path allows you
    to get information about the mounted vPower NFS datastore, such as restore session ID, mount point
    state, instant FCD recovery settings and disks that will be recovered.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam
    Backup Viewer.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | VmwareFcdInstantRecoveryMount
    """

    return (
        await asyncio_detailed(
            mount_id=mount_id,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed

from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.empty_success_response import EmptySuccessResponse
from ...models.error import Error
from ...models.vi_vm_snapshot_replica_change_switchover_time_failback_spec import (
    ViVMSnapshotReplicaChangeSwitchoverTimeFailbackSpec,
)
from ...types import Response


def _get_kwargs(
    *,
    body: ViVMSnapshotReplicaChangeSwitchoverTimeFailbackSpec,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/failback/changeSwitchoverTime/vSphere/snapshot",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EmptySuccessResponse | Error | None:
    if response.status_code == 200:
        response_200 = EmptySuccessResponse.from_dict(response.json())

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
) -> Response[EmptySuccessResponse | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ViVMSnapshotReplicaChangeSwitchoverTimeFailbackSpec,
    x_api_version: str = "1.3-rev1",
) -> Response[EmptySuccessResponse | Error]:
    """Change Switchover Time

     The HTTP POST request to the `/api/v1/failback/changeSwitchoverTime/vSphere/snapshot` endpoint
    changes the time when you want to switch over from snapshot replicas to production VMware vSphere
    VMs.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (ViVMSnapshotReplicaChangeSwitchoverTimeFailbackSpec): Settings for changing
            switchover time.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EmptySuccessResponse | Error]
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
    body: ViVMSnapshotReplicaChangeSwitchoverTimeFailbackSpec,
    x_api_version: str = "1.3-rev1",
) -> EmptySuccessResponse | Error | None:
    """Change Switchover Time

     The HTTP POST request to the `/api/v1/failback/changeSwitchoverTime/vSphere/snapshot` endpoint
    changes the time when you want to switch over from snapshot replicas to production VMware vSphere
    VMs.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (ViVMSnapshotReplicaChangeSwitchoverTimeFailbackSpec): Settings for changing
            switchover time.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EmptySuccessResponse | Error
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ViVMSnapshotReplicaChangeSwitchoverTimeFailbackSpec,
    x_api_version: str = "1.3-rev1",
) -> Response[EmptySuccessResponse | Error]:
    """Change Switchover Time

     The HTTP POST request to the `/api/v1/failback/changeSwitchoverTime/vSphere/snapshot` endpoint
    changes the time when you want to switch over from snapshot replicas to production VMware vSphere
    VMs.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (ViVMSnapshotReplicaChangeSwitchoverTimeFailbackSpec): Settings for changing
            switchover time.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EmptySuccessResponse | Error]
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
    body: ViVMSnapshotReplicaChangeSwitchoverTimeFailbackSpec,
    x_api_version: str = "1.3-rev1",
) -> EmptySuccessResponse | Error | None:
    """Change Switchover Time

     The HTTP POST request to the `/api/v1/failback/changeSwitchoverTime/vSphere/snapshot` endpoint
    changes the time when you want to switch over from snapshot replicas to production VMware vSphere
    VMs.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (ViVMSnapshotReplicaChangeSwitchoverTimeFailbackSpec): Settings for changing
            switchover time.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EmptySuccessResponse | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

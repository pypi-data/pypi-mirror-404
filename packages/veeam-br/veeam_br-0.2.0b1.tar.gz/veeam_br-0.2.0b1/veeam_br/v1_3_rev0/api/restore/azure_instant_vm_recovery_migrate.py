from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.azure_instant_vm_recovery_migration_spec import AzureInstantVMRecoveryMigrationSpec
from ...models.azure_instant_vm_recovery_mount import AzureInstantVMRecoveryMount
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    mount_id: UUID,
    *,
    body: AzureInstantVMRecoveryMigrationSpec,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/restore/instantRecovery/azure/vm/{mount_id}/migrate".format(
            mount_id=quote(str(mount_id), safe=""),
        ),
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
    mount_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: AzureInstantVMRecoveryMigrationSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[AzureInstantVMRecoveryMount | Error]:
    """Start Migrating Machine to Azure

     The HTTP POST request to the `/api/v1/restore/instantRecovery/azure/vm/{mountId}/migrate` path
    allows you to start VM migration from the specified mount.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (AzureInstantVMRecoveryMigrationSpec): Migration settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AzureInstantVMRecoveryMount | Error]
    """

    kwargs = _get_kwargs(
        mount_id=mount_id,
        body=body,
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
    body: AzureInstantVMRecoveryMigrationSpec,
    x_api_version: str = "1.3-rev0",
) -> AzureInstantVMRecoveryMount | Error | None:
    """Start Migrating Machine to Azure

     The HTTP POST request to the `/api/v1/restore/instantRecovery/azure/vm/{mountId}/migrate` path
    allows you to start VM migration from the specified mount.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (AzureInstantVMRecoveryMigrationSpec): Migration settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AzureInstantVMRecoveryMount | Error
    """

    return sync_detailed(
        mount_id=mount_id,
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    mount_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: AzureInstantVMRecoveryMigrationSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[AzureInstantVMRecoveryMount | Error]:
    """Start Migrating Machine to Azure

     The HTTP POST request to the `/api/v1/restore/instantRecovery/azure/vm/{mountId}/migrate` path
    allows you to start VM migration from the specified mount.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (AzureInstantVMRecoveryMigrationSpec): Migration settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AzureInstantVMRecoveryMount | Error]
    """

    kwargs = _get_kwargs(
        mount_id=mount_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    mount_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: AzureInstantVMRecoveryMigrationSpec,
    x_api_version: str = "1.3-rev0",
) -> AzureInstantVMRecoveryMount | Error | None:
    """Start Migrating Machine to Azure

     The HTTP POST request to the `/api/v1/restore/instantRecovery/azure/vm/{mountId}/migrate` path
    allows you to start VM migration from the specified mount.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (AzureInstantVMRecoveryMigrationSpec): Migration settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AzureInstantVMRecoveryMount | Error
    """

    return (
        await asyncio_detailed(
            mount_id=mount_id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

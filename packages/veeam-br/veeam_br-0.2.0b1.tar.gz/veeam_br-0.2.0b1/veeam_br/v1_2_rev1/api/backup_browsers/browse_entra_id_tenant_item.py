from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.entra_id_tenant_browse_model import EntraIdTenantBrowseModel
from ...models.entra_id_tenant_item_type_spec import EntraIdTenantItemTypeSpec
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    backup_id: UUID,
    item_id: str,
    *,
    body: EntraIdTenantItemTypeSpec,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backupBrowser/entraIdTenant/{backup_id}/browse/{item_id}".format(
            backup_id=quote(str(backup_id), safe=""),
            item_id=quote(str(item_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EntraIdTenantBrowseModel | Error | None:
    if response.status_code == 200:
        response_200 = EntraIdTenantBrowseModel.from_dict(response.json())

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
) -> Response[EntraIdTenantBrowseModel | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    backup_id: UUID,
    item_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EntraIdTenantItemTypeSpec,
    x_api_version: str = "1.2-rev1",
) -> Response[EntraIdTenantBrowseModel | Error]:
    """Get Microsoft Entra ID Item

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/browse/{itemId}` path
    allows you to get a specific Microsoft Entra ID item available in a tenant backup that has the
    specified `backupId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        backup_id (UUID):
        item_id (str):
        x_api_version (str):  Default: '1.2-rev1'.
        body (EntraIdTenantItemTypeSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EntraIdTenantBrowseModel | Error]
    """

    kwargs = _get_kwargs(
        backup_id=backup_id,
        item_id=item_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    backup_id: UUID,
    item_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EntraIdTenantItemTypeSpec,
    x_api_version: str = "1.2-rev1",
) -> EntraIdTenantBrowseModel | Error | None:
    """Get Microsoft Entra ID Item

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/browse/{itemId}` path
    allows you to get a specific Microsoft Entra ID item available in a tenant backup that has the
    specified `backupId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        backup_id (UUID):
        item_id (str):
        x_api_version (str):  Default: '1.2-rev1'.
        body (EntraIdTenantItemTypeSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EntraIdTenantBrowseModel | Error
    """

    return sync_detailed(
        backup_id=backup_id,
        item_id=item_id,
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    backup_id: UUID,
    item_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EntraIdTenantItemTypeSpec,
    x_api_version: str = "1.2-rev1",
) -> Response[EntraIdTenantBrowseModel | Error]:
    """Get Microsoft Entra ID Item

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/browse/{itemId}` path
    allows you to get a specific Microsoft Entra ID item available in a tenant backup that has the
    specified `backupId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        backup_id (UUID):
        item_id (str):
        x_api_version (str):  Default: '1.2-rev1'.
        body (EntraIdTenantItemTypeSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EntraIdTenantBrowseModel | Error]
    """

    kwargs = _get_kwargs(
        backup_id=backup_id,
        item_id=item_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    backup_id: UUID,
    item_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EntraIdTenantItemTypeSpec,
    x_api_version: str = "1.2-rev1",
) -> EntraIdTenantBrowseModel | Error | None:
    """Get Microsoft Entra ID Item

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/browse/{itemId}` path
    allows you to get a specific Microsoft Entra ID item available in a tenant backup that has the
    specified `backupId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        backup_id (UUID):
        item_id (str):
        x_api_version (str):  Default: '1.2-rev1'.
        body (EntraIdTenantItemTypeSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EntraIdTenantBrowseModel | Error
    """

    return (
        await asyncio_detailed(
            backup_id=backup_id,
            item_id=item_id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

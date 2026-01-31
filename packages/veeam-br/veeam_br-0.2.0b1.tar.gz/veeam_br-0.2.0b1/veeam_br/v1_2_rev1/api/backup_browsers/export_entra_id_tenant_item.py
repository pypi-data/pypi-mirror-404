from http import HTTPStatus
from io import BytesIO
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.entra_id_tenant_browse_spec import EntraIdTenantBrowseSpec
from ...models.error import Error
from ...types import UNSET, File, Response, Unset


def _get_kwargs(
    backup_id: UUID,
    *,
    body: EntraIdTenantBrowseSpec,
    to_xml: bool | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    params["toXml"] = to_xml

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backupBrowser/entraIdTenant/{backup_id}/export".format(
            backup_id=quote(str(backup_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Error | File | None:
    if response.status_code == 200:
        response_200 = File(payload=BytesIO(response.content))

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Error | File]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    backup_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: EntraIdTenantBrowseSpec,
    to_xml: bool | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | File]:
    """Export Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/export` path allows you
    to export Microsoft Entra ID items from backup that has the specified `backupId` to an XML or CSV
    file. The exported file contains all item properties that are available in the backup.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        backup_id (UUID):
        to_xml (bool | Unset):
        x_api_version (str):  Default: '1.2-rev1'.
        body (EntraIdTenantBrowseSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | File]
    """

    kwargs = _get_kwargs(
        backup_id=backup_id,
        body=body,
        to_xml=to_xml,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    backup_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: EntraIdTenantBrowseSpec,
    to_xml: bool | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Error | File | None:
    """Export Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/export` path allows you
    to export Microsoft Entra ID items from backup that has the specified `backupId` to an XML or CSV
    file. The exported file contains all item properties that are available in the backup.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        backup_id (UUID):
        to_xml (bool | Unset):
        x_api_version (str):  Default: '1.2-rev1'.
        body (EntraIdTenantBrowseSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | File
    """

    return sync_detailed(
        backup_id=backup_id,
        client=client,
        body=body,
        to_xml=to_xml,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    backup_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: EntraIdTenantBrowseSpec,
    to_xml: bool | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | File]:
    """Export Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/export` path allows you
    to export Microsoft Entra ID items from backup that has the specified `backupId` to an XML or CSV
    file. The exported file contains all item properties that are available in the backup.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        backup_id (UUID):
        to_xml (bool | Unset):
        x_api_version (str):  Default: '1.2-rev1'.
        body (EntraIdTenantBrowseSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | File]
    """

    kwargs = _get_kwargs(
        backup_id=backup_id,
        body=body,
        to_xml=to_xml,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    backup_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: EntraIdTenantBrowseSpec,
    to_xml: bool | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Error | File | None:
    """Export Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/export` path allows you
    to export Microsoft Entra ID items from backup that has the specified `backupId` to an XML or CSV
    file. The exported file contains all item properties that are available in the backup.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        backup_id (UUID):
        to_xml (bool | Unset):
        x_api_version (str):  Default: '1.2-rev1'.
        body (EntraIdTenantBrowseSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | File
    """

    return (
        await asyncio_detailed(
            backup_id=backup_id,
            client=client,
            body=body,
            to_xml=to_xml,
            x_api_version=x_api_version,
        )
    ).parsed

from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.entra_id_tenant_restore_device_code_state_model import EntraIdTenantRestoreDeviceCodeStateModel
from ...models.entra_id_tenant_restore_device_code_state_spec import EntraIdTenantRestoreDeviceCodeStateSpec
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    *,
    body: EntraIdTenantRestoreDeviceCodeStateSpec,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/restore/entraId/tenant/deviceCode/state",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EntraIdTenantRestoreDeviceCodeStateModel | Error | None:
    if response.status_code == 200:
        response_200 = EntraIdTenantRestoreDeviceCodeStateModel.from_dict(response.json())

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
) -> Response[EntraIdTenantRestoreDeviceCodeStateModel | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: EntraIdTenantRestoreDeviceCodeStateSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[EntraIdTenantRestoreDeviceCodeStateModel | Error]:
    """Get Credentials for Delegated Restore of Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/restore/entraId/tenant/deviceCode/state` path allows you to
    get credentials that are required for delegated restore of Microsoft Entra ID items. Before you
    request the credentials, obtain a user code using the [Get User Code for Microsoft Entra ID Item
    Restore](Restore#operation/GetEntraIdTenantRestoreDeviceCode) request.<p>You can use the credentials
    in the following requests&#58;</p> <ul><li>[Restore Microsoft Entra ID Items](Backup-
    Browsers#operation/RestoreEntraIdTenantItems)</li> <li>[Restore Microsoft Entra ID Item
    Properties](Backup-Browsers#operation/RestoreEntraIdTenantItemAttributes)</li> </ul><p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (EntraIdTenantRestoreDeviceCodeStateSpec): User code state settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EntraIdTenantRestoreDeviceCodeStateModel | Error]
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
    body: EntraIdTenantRestoreDeviceCodeStateSpec,
    x_api_version: str = "1.3-rev0",
) -> EntraIdTenantRestoreDeviceCodeStateModel | Error | None:
    """Get Credentials for Delegated Restore of Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/restore/entraId/tenant/deviceCode/state` path allows you to
    get credentials that are required for delegated restore of Microsoft Entra ID items. Before you
    request the credentials, obtain a user code using the [Get User Code for Microsoft Entra ID Item
    Restore](Restore#operation/GetEntraIdTenantRestoreDeviceCode) request.<p>You can use the credentials
    in the following requests&#58;</p> <ul><li>[Restore Microsoft Entra ID Items](Backup-
    Browsers#operation/RestoreEntraIdTenantItems)</li> <li>[Restore Microsoft Entra ID Item
    Properties](Backup-Browsers#operation/RestoreEntraIdTenantItemAttributes)</li> </ul><p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (EntraIdTenantRestoreDeviceCodeStateSpec): User code state settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EntraIdTenantRestoreDeviceCodeStateModel | Error
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: EntraIdTenantRestoreDeviceCodeStateSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[EntraIdTenantRestoreDeviceCodeStateModel | Error]:
    """Get Credentials for Delegated Restore of Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/restore/entraId/tenant/deviceCode/state` path allows you to
    get credentials that are required for delegated restore of Microsoft Entra ID items. Before you
    request the credentials, obtain a user code using the [Get User Code for Microsoft Entra ID Item
    Restore](Restore#operation/GetEntraIdTenantRestoreDeviceCode) request.<p>You can use the credentials
    in the following requests&#58;</p> <ul><li>[Restore Microsoft Entra ID Items](Backup-
    Browsers#operation/RestoreEntraIdTenantItems)</li> <li>[Restore Microsoft Entra ID Item
    Properties](Backup-Browsers#operation/RestoreEntraIdTenantItemAttributes)</li> </ul><p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (EntraIdTenantRestoreDeviceCodeStateSpec): User code state settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EntraIdTenantRestoreDeviceCodeStateModel | Error]
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
    body: EntraIdTenantRestoreDeviceCodeStateSpec,
    x_api_version: str = "1.3-rev0",
) -> EntraIdTenantRestoreDeviceCodeStateModel | Error | None:
    """Get Credentials for Delegated Restore of Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/restore/entraId/tenant/deviceCode/state` path allows you to
    get credentials that are required for delegated restore of Microsoft Entra ID items. Before you
    request the credentials, obtain a user code using the [Get User Code for Microsoft Entra ID Item
    Restore](Restore#operation/GetEntraIdTenantRestoreDeviceCode) request.<p>You can use the credentials
    in the following requests&#58;</p> <ul><li>[Restore Microsoft Entra ID Items](Backup-
    Browsers#operation/RestoreEntraIdTenantItems)</li> <li>[Restore Microsoft Entra ID Item
    Properties](Backup-Browsers#operation/RestoreEntraIdTenantItemAttributes)</li> </ul><p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (EntraIdTenantRestoreDeviceCodeStateSpec): User code state settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EntraIdTenantRestoreDeviceCodeStateModel | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

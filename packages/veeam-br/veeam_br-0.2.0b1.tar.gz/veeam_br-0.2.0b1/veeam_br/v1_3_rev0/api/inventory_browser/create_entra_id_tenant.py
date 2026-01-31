from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.entra_id_tenant_spec import EntraIDTenantSpec
from ...models.error import Error
from ...models.session_model import SessionModel
from ...types import Response


def _get_kwargs(
    *,
    body: EntraIDTenantSpec,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/inventory/entraId/tenants",
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
    body: EntraIDTenantSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | SessionModel]:
    """Add Microsoft Entra ID Tenant

     The HTTP POST request to the `/api/v1/inventory/entraId/tenants` path allows you to add a Microsoft
    Entra ID tenant to the backup server. <p>When adding a tenant, specify an existing Microsoft Entra
    ID app registration or let Veeam Backup & Replication create a new one. If you choose to create a
    new app registration, you must generate a verification code and register the new application before
    you start adding a tenant&#58; <ol><li>To generate a code, use the [Get Microsoft Entra ID
    Verification Code](Credentials#operation/RequestAppRegistrationByDeviceCode) request.</li> <li>To
    register the new application, use the [Register Microsoft Entra ID
    Application](Credentials#operation/FinishAppRegistrationByDeviceCode) request.</li></ol></p> <p>
    **Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (EntraIDTenantSpec): Settings for Entra ID tenant.

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
    body: EntraIDTenantSpec,
    x_api_version: str = "1.3-rev0",
) -> Error | SessionModel | None:
    """Add Microsoft Entra ID Tenant

     The HTTP POST request to the `/api/v1/inventory/entraId/tenants` path allows you to add a Microsoft
    Entra ID tenant to the backup server. <p>When adding a tenant, specify an existing Microsoft Entra
    ID app registration or let Veeam Backup & Replication create a new one. If you choose to create a
    new app registration, you must generate a verification code and register the new application before
    you start adding a tenant&#58; <ol><li>To generate a code, use the [Get Microsoft Entra ID
    Verification Code](Credentials#operation/RequestAppRegistrationByDeviceCode) request.</li> <li>To
    register the new application, use the [Register Microsoft Entra ID
    Application](Credentials#operation/FinishAppRegistrationByDeviceCode) request.</li></ol></p> <p>
    **Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (EntraIDTenantSpec): Settings for Entra ID tenant.

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
    body: EntraIDTenantSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | SessionModel]:
    """Add Microsoft Entra ID Tenant

     The HTTP POST request to the `/api/v1/inventory/entraId/tenants` path allows you to add a Microsoft
    Entra ID tenant to the backup server. <p>When adding a tenant, specify an existing Microsoft Entra
    ID app registration or let Veeam Backup & Replication create a new one. If you choose to create a
    new app registration, you must generate a verification code and register the new application before
    you start adding a tenant&#58; <ol><li>To generate a code, use the [Get Microsoft Entra ID
    Verification Code](Credentials#operation/RequestAppRegistrationByDeviceCode) request.</li> <li>To
    register the new application, use the [Register Microsoft Entra ID
    Application](Credentials#operation/FinishAppRegistrationByDeviceCode) request.</li></ol></p> <p>
    **Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (EntraIDTenantSpec): Settings for Entra ID tenant.

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
    body: EntraIDTenantSpec,
    x_api_version: str = "1.3-rev0",
) -> Error | SessionModel | None:
    """Add Microsoft Entra ID Tenant

     The HTTP POST request to the `/api/v1/inventory/entraId/tenants` path allows you to add a Microsoft
    Entra ID tenant to the backup server. <p>When adding a tenant, specify an existing Microsoft Entra
    ID app registration or let Veeam Backup & Replication create a new one. If you choose to create a
    new app registration, you must generate a verification code and register the new application before
    you start adding a tenant&#58; <ol><li>To generate a code, use the [Get Microsoft Entra ID
    Verification Code](Credentials#operation/RequestAppRegistrationByDeviceCode) request.</li> <li>To
    register the new application, use the [Register Microsoft Entra ID
    Application](Credentials#operation/FinishAppRegistrationByDeviceCode) request.</li></ol></p> <p>
    **Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (EntraIDTenantSpec): Settings for Entra ID tenant.

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

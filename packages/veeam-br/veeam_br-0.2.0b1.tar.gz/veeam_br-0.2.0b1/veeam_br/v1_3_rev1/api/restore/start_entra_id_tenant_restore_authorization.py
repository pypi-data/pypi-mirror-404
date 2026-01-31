from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.entra_id_tenant_restore_start_authorization_model import EntraIdTenantRestoreStartAuthorizationModel
from ...models.error import Error
from ...types import UNSET, Response


def _get_kwargs(
    session_id: UUID,
    *,
    vdc_session_id: str,
    redirect_uri: str,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    params["vdcSessionId"] = vdc_session_id

    params["redirectUri"] = redirect_uri

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/restore/entraId/tenant/{session_id}/authCode/startAuthorization".format(
            session_id=quote(str(session_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EntraIdTenantRestoreStartAuthorizationModel | Error | None:
    if response.status_code == 200:
        response_200 = EntraIdTenantRestoreStartAuthorizationModel.from_dict(response.json())

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
) -> Response[EntraIdTenantRestoreStartAuthorizationModel | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    session_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    vdc_session_id: str,
    redirect_uri: str,
    x_api_version: str = "1.3-rev1",
) -> Response[EntraIdTenantRestoreStartAuthorizationModel | Error]:
    r"""Get Redirect URI for Delegated Restore of Microsoft Entra ID Items

     The HTTP GET request to the `/api/v1/restore/entraId/tenant/{sessionId}/authCode/startAuthorization`
    endpoint obtains a redirect URI required to perform authorization code flow for delegated restore of
    Microsoft Entra ID items.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>\"

    Args:
        session_id (UUID):
        vdc_session_id (str):
        redirect_uri (str):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EntraIdTenantRestoreStartAuthorizationModel | Error]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        vdc_session_id=vdc_session_id,
        redirect_uri=redirect_uri,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    session_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    vdc_session_id: str,
    redirect_uri: str,
    x_api_version: str = "1.3-rev1",
) -> EntraIdTenantRestoreStartAuthorizationModel | Error | None:
    r"""Get Redirect URI for Delegated Restore of Microsoft Entra ID Items

     The HTTP GET request to the `/api/v1/restore/entraId/tenant/{sessionId}/authCode/startAuthorization`
    endpoint obtains a redirect URI required to perform authorization code flow for delegated restore of
    Microsoft Entra ID items.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>\"

    Args:
        session_id (UUID):
        vdc_session_id (str):
        redirect_uri (str):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EntraIdTenantRestoreStartAuthorizationModel | Error
    """

    return sync_detailed(
        session_id=session_id,
        client=client,
        vdc_session_id=vdc_session_id,
        redirect_uri=redirect_uri,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    session_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    vdc_session_id: str,
    redirect_uri: str,
    x_api_version: str = "1.3-rev1",
) -> Response[EntraIdTenantRestoreStartAuthorizationModel | Error]:
    r"""Get Redirect URI for Delegated Restore of Microsoft Entra ID Items

     The HTTP GET request to the `/api/v1/restore/entraId/tenant/{sessionId}/authCode/startAuthorization`
    endpoint obtains a redirect URI required to perform authorization code flow for delegated restore of
    Microsoft Entra ID items.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>\"

    Args:
        session_id (UUID):
        vdc_session_id (str):
        redirect_uri (str):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EntraIdTenantRestoreStartAuthorizationModel | Error]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        vdc_session_id=vdc_session_id,
        redirect_uri=redirect_uri,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    session_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    vdc_session_id: str,
    redirect_uri: str,
    x_api_version: str = "1.3-rev1",
) -> EntraIdTenantRestoreStartAuthorizationModel | Error | None:
    r"""Get Redirect URI for Delegated Restore of Microsoft Entra ID Items

     The HTTP GET request to the `/api/v1/restore/entraId/tenant/{sessionId}/authCode/startAuthorization`
    endpoint obtains a redirect URI required to perform authorization code flow for delegated restore of
    Microsoft Entra ID items.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>\"

    Args:
        session_id (UUID):
        vdc_session_id (str):
        redirect_uri (str):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EntraIdTenantRestoreStartAuthorizationModel | Error
    """

    return (
        await asyncio_detailed(
            session_id=session_id,
            client=client,
            vdc_session_id=vdc_session_id,
            redirect_uri=redirect_uri,
            x_api_version=x_api_version,
        )
    ).parsed

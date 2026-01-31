from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.entra_id_tenant_restore_sessions_result import EntraIdTenantRestoreSessionsResult
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    session_id: UUID,
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    params["skip"] = skip

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/backupBrowser/entraIdTenant/{session_id}/restoreSessions".format(
            session_id=quote(str(session_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EntraIdTenantRestoreSessionsResult | Error | None:
    if response.status_code == 200:
        response_200 = EntraIdTenantRestoreSessionsResult.from_dict(response.json())

        return response_200

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
) -> Response[EntraIdTenantRestoreSessionsResult | Error]:
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
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    x_api_version: str = "1.3-rev1",
) -> Response[EntraIdTenantRestoreSessionsResult | Error]:
    """Get All Restore Sessions of Microsoft Entra ID Tenant

     The HTTP GET request to the `/api/v1/backupBrowser/entraIdTenant/{sessionId}/restoreSessions`
    endpoint gets an array of restore sessions that were started for a Microsoft Entra ID tenant mount
    point with the specified `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Restore Operator.</p>

    Args:
        session_id (UUID):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EntraIdTenantRestoreSessionsResult | Error]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        skip=skip,
        limit=limit,
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
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    x_api_version: str = "1.3-rev1",
) -> EntraIdTenantRestoreSessionsResult | Error | None:
    """Get All Restore Sessions of Microsoft Entra ID Tenant

     The HTTP GET request to the `/api/v1/backupBrowser/entraIdTenant/{sessionId}/restoreSessions`
    endpoint gets an array of restore sessions that were started for a Microsoft Entra ID tenant mount
    point with the specified `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Restore Operator.</p>

    Args:
        session_id (UUID):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EntraIdTenantRestoreSessionsResult | Error
    """

    return sync_detailed(
        session_id=session_id,
        client=client,
        skip=skip,
        limit=limit,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    session_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    x_api_version: str = "1.3-rev1",
) -> Response[EntraIdTenantRestoreSessionsResult | Error]:
    """Get All Restore Sessions of Microsoft Entra ID Tenant

     The HTTP GET request to the `/api/v1/backupBrowser/entraIdTenant/{sessionId}/restoreSessions`
    endpoint gets an array of restore sessions that were started for a Microsoft Entra ID tenant mount
    point with the specified `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Restore Operator.</p>

    Args:
        session_id (UUID):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EntraIdTenantRestoreSessionsResult | Error]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        skip=skip,
        limit=limit,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    session_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    x_api_version: str = "1.3-rev1",
) -> EntraIdTenantRestoreSessionsResult | Error | None:
    """Get All Restore Sessions of Microsoft Entra ID Tenant

     The HTTP GET request to the `/api/v1/backupBrowser/entraIdTenant/{sessionId}/restoreSessions`
    endpoint gets an array of restore sessions that were started for a Microsoft Entra ID tenant mount
    point with the specified `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Restore Operator.</p>

    Args:
        session_id (UUID):
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EntraIdTenantRestoreSessionsResult | Error
    """

    return (
        await asyncio_detailed(
            session_id=session_id,
            client=client,
            skip=skip,
            limit=limit,
            x_api_version=x_api_version,
        )
    ).parsed

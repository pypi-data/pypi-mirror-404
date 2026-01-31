from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.entra_id_tenant_validate_model import EntraIdTenantValidateModel
from ...models.entra_id_tenant_validate_spec import EntraIdTenantValidateSpec
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    session_id: UUID,
    *,
    body: EntraIdTenantValidateSpec,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backupBrowser/entraIdTenant/{session_id}/validate".format(
            session_id=quote(str(session_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EntraIdTenantValidateModel | Error | None:
    if response.status_code == 200:
        response_200 = EntraIdTenantValidateModel.from_dict(response.json())

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
) -> Response[EntraIdTenantValidateModel | Error]:
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
    body: EntraIdTenantValidateSpec,
    x_api_version: str = "1.2-rev1",
) -> Response[EntraIdTenantValidateModel | Error]:
    """Validate Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{sessionId}/validate` path allows
    you to validate that Microsoft Entra ID items specified in the request body are available in a
    specified restore point.<p>In the response body, you receive an array of items that are missing in
    the restore point. To browse restore points that are available for each of the missing items, use
    the [Get Restore Points of Microsoft Entra ID
    Item](#tag/BackupBrowsers/operation/BrowseEntraIdTenantRestorePoints) request.</p><p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (EntraIdTenantValidateSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EntraIdTenantValidateModel | Error]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        body=body,
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
    body: EntraIdTenantValidateSpec,
    x_api_version: str = "1.2-rev1",
) -> EntraIdTenantValidateModel | Error | None:
    """Validate Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{sessionId}/validate` path allows
    you to validate that Microsoft Entra ID items specified in the request body are available in a
    specified restore point.<p>In the response body, you receive an array of items that are missing in
    the restore point. To browse restore points that are available for each of the missing items, use
    the [Get Restore Points of Microsoft Entra ID
    Item](#tag/BackupBrowsers/operation/BrowseEntraIdTenantRestorePoints) request.</p><p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (EntraIdTenantValidateSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EntraIdTenantValidateModel | Error
    """

    return sync_detailed(
        session_id=session_id,
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    session_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: EntraIdTenantValidateSpec,
    x_api_version: str = "1.2-rev1",
) -> Response[EntraIdTenantValidateModel | Error]:
    """Validate Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{sessionId}/validate` path allows
    you to validate that Microsoft Entra ID items specified in the request body are available in a
    specified restore point.<p>In the response body, you receive an array of items that are missing in
    the restore point. To browse restore points that are available for each of the missing items, use
    the [Get Restore Points of Microsoft Entra ID
    Item](#tag/BackupBrowsers/operation/BrowseEntraIdTenantRestorePoints) request.</p><p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (EntraIdTenantValidateSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EntraIdTenantValidateModel | Error]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    session_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: EntraIdTenantValidateSpec,
    x_api_version: str = "1.2-rev1",
) -> EntraIdTenantValidateModel | Error | None:
    """Validate Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{sessionId}/validate` path allows
    you to validate that Microsoft Entra ID items specified in the request body are available in a
    specified restore point.<p>In the response body, you receive an array of items that are missing in
    the restore point. To browse restore points that are available for each of the missing items, use
    the [Get Restore Points of Microsoft Entra ID
    Item](#tag/BackupBrowsers/operation/BrowseEntraIdTenantRestorePoints) request.</p><p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (EntraIdTenantValidateSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EntraIdTenantValidateModel | Error
    """

    return (
        await asyncio_detailed(
            session_id=session_id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

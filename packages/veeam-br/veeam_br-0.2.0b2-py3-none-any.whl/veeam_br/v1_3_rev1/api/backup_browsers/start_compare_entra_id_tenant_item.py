from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.entra_id_tenant_item_comparison_spec import EntraIdTenantItemComparisonSpec
from ...models.entra_id_tenant_item_start_comparison_model import EntraIdTenantItemStartComparisonModel
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    session_id: UUID,
    *,
    body: EntraIdTenantItemComparisonSpec,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backupBrowser/entraIdTenant/{session_id}/startCompare".format(
            session_id=quote(str(session_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EntraIdTenantItemStartComparisonModel | Error | None:
    if response.status_code == 200:
        response_200 = EntraIdTenantItemStartComparisonModel.from_dict(response.json())

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
) -> Response[EntraIdTenantItemStartComparisonModel | Error]:
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
    body: EntraIdTenantItemComparisonSpec,
    x_api_version: str = "1.3-rev1",
) -> Response[EntraIdTenantItemStartComparisonModel | Error]:
    """Start Comparing Microsoft Entra ID Item Properties

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{sessionId}/startCompare` endpoint
    starts comparing the properties of a Microsoft Entra ID item available in a mount session that has
    the specified `sessionId`.<p>You can compare item properties either between 2 restore points or
    between a restore point and production. To compare the item to production, do not specify
    `newRestorePointId`.</p><p>This request is asynchronous, meaning that the request returns a
    comparison session immediately so the client can continue execution, and you can process the
    comparison results later when the session changes its state to `Success`. To get the comparison
    results, run the [Get Comparison Results for Microsoft Entra ID Items](Backup-
    Browsers#operation/GetCompareEntraIdTenantItemResult) request. For details on synchronous request,
    see [Compare Microsoft Entra ID Item Properties](Backup-
    Browsers#operation/CompareEntraIdTenantItem).</p>**Available to**&#58; Veeam Backup Administrator,
    Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (EntraIdTenantItemComparisonSpec): Settings for comparing Microsoft Entra ID item
            properties.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EntraIdTenantItemStartComparisonModel | Error]
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
    body: EntraIdTenantItemComparisonSpec,
    x_api_version: str = "1.3-rev1",
) -> EntraIdTenantItemStartComparisonModel | Error | None:
    """Start Comparing Microsoft Entra ID Item Properties

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{sessionId}/startCompare` endpoint
    starts comparing the properties of a Microsoft Entra ID item available in a mount session that has
    the specified `sessionId`.<p>You can compare item properties either between 2 restore points or
    between a restore point and production. To compare the item to production, do not specify
    `newRestorePointId`.</p><p>This request is asynchronous, meaning that the request returns a
    comparison session immediately so the client can continue execution, and you can process the
    comparison results later when the session changes its state to `Success`. To get the comparison
    results, run the [Get Comparison Results for Microsoft Entra ID Items](Backup-
    Browsers#operation/GetCompareEntraIdTenantItemResult) request. For details on synchronous request,
    see [Compare Microsoft Entra ID Item Properties](Backup-
    Browsers#operation/CompareEntraIdTenantItem).</p>**Available to**&#58; Veeam Backup Administrator,
    Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (EntraIdTenantItemComparisonSpec): Settings for comparing Microsoft Entra ID item
            properties.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EntraIdTenantItemStartComparisonModel | Error
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
    body: EntraIdTenantItemComparisonSpec,
    x_api_version: str = "1.3-rev1",
) -> Response[EntraIdTenantItemStartComparisonModel | Error]:
    """Start Comparing Microsoft Entra ID Item Properties

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{sessionId}/startCompare` endpoint
    starts comparing the properties of a Microsoft Entra ID item available in a mount session that has
    the specified `sessionId`.<p>You can compare item properties either between 2 restore points or
    between a restore point and production. To compare the item to production, do not specify
    `newRestorePointId`.</p><p>This request is asynchronous, meaning that the request returns a
    comparison session immediately so the client can continue execution, and you can process the
    comparison results later when the session changes its state to `Success`. To get the comparison
    results, run the [Get Comparison Results for Microsoft Entra ID Items](Backup-
    Browsers#operation/GetCompareEntraIdTenantItemResult) request. For details on synchronous request,
    see [Compare Microsoft Entra ID Item Properties](Backup-
    Browsers#operation/CompareEntraIdTenantItem).</p>**Available to**&#58; Veeam Backup Administrator,
    Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (EntraIdTenantItemComparisonSpec): Settings for comparing Microsoft Entra ID item
            properties.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EntraIdTenantItemStartComparisonModel | Error]
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
    body: EntraIdTenantItemComparisonSpec,
    x_api_version: str = "1.3-rev1",
) -> EntraIdTenantItemStartComparisonModel | Error | None:
    """Start Comparing Microsoft Entra ID Item Properties

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{sessionId}/startCompare` endpoint
    starts comparing the properties of a Microsoft Entra ID item available in a mount session that has
    the specified `sessionId`.<p>You can compare item properties either between 2 restore points or
    between a restore point and production. To compare the item to production, do not specify
    `newRestorePointId`.</p><p>This request is asynchronous, meaning that the request returns a
    comparison session immediately so the client can continue execution, and you can process the
    comparison results later when the session changes its state to `Success`. To get the comparison
    results, run the [Get Comparison Results for Microsoft Entra ID Items](Backup-
    Browsers#operation/GetCompareEntraIdTenantItemResult) request. For details on synchronous request,
    see [Compare Microsoft Entra ID Item Properties](Backup-
    Browsers#operation/CompareEntraIdTenantItem).</p>**Available to**&#58; Veeam Backup Administrator,
    Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (EntraIdTenantItemComparisonSpec): Settings for comparing Microsoft Entra ID item
            properties.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EntraIdTenantItemStartComparisonModel | Error
    """

    return (
        await asyncio_detailed(
            session_id=session_id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

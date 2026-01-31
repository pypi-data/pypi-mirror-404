from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_recovery_media_format import ERecoveryMediaFormat
from ...models.error import Error
from ...types import UNSET, Response


def _get_kwargs(
    id: UUID,
    entity_id: UUID,
    *,
    format_: ERecoveryMediaFormat,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    json_format_ = format_.value
    params["format"] = json_format_

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/agents/protectionGroups/{id}/discoveredEntities/{entity_id}/createRecoveryMedia".format(
            id=quote(str(id), safe=""),
            entity_id=quote(str(entity_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Error | None:
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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: UUID,
    entity_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    format_: ERecoveryMediaFormat,
    x_api_version: str = "1.3-rev1",
) -> Response[Error]:
    """Create Recovery Media for Discovered Entity

     The HTTP GET request to the
    `/api/v1/agents/protectionGroups/{id}/discoveredEntities/{entityId}/createRecoveryMedia` endpoint
    creates Veeam Recovery Media for a protected Microsoft Windows computer. The request will create an
    ISO file that you can boot from in case the computer stops working or the hard disk fails.<p>You can
    also create Veeam Recovery Media for a backup created by Veeam Agent for Microsoft Windows. For more
    information, see [Create Recovery Media for Backup](Backup-
    Objects#operation/CreateRecoveryMediaForBackupObject). <p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        id (UUID):
        entity_id (UUID):
        format_ (ERecoveryMediaFormat): Recovery media format.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error]
    """

    kwargs = _get_kwargs(
        id=id,
        entity_id=entity_id,
        format_=format_,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: UUID,
    entity_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    format_: ERecoveryMediaFormat,
    x_api_version: str = "1.3-rev1",
) -> Error | None:
    """Create Recovery Media for Discovered Entity

     The HTTP GET request to the
    `/api/v1/agents/protectionGroups/{id}/discoveredEntities/{entityId}/createRecoveryMedia` endpoint
    creates Veeam Recovery Media for a protected Microsoft Windows computer. The request will create an
    ISO file that you can boot from in case the computer stops working or the hard disk fails.<p>You can
    also create Veeam Recovery Media for a backup created by Veeam Agent for Microsoft Windows. For more
    information, see [Create Recovery Media for Backup](Backup-
    Objects#operation/CreateRecoveryMediaForBackupObject). <p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        id (UUID):
        entity_id (UUID):
        format_ (ERecoveryMediaFormat): Recovery media format.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error
    """

    return sync_detailed(
        id=id,
        entity_id=entity_id,
        client=client,
        format_=format_,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    entity_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    format_: ERecoveryMediaFormat,
    x_api_version: str = "1.3-rev1",
) -> Response[Error]:
    """Create Recovery Media for Discovered Entity

     The HTTP GET request to the
    `/api/v1/agents/protectionGroups/{id}/discoveredEntities/{entityId}/createRecoveryMedia` endpoint
    creates Veeam Recovery Media for a protected Microsoft Windows computer. The request will create an
    ISO file that you can boot from in case the computer stops working or the hard disk fails.<p>You can
    also create Veeam Recovery Media for a backup created by Veeam Agent for Microsoft Windows. For more
    information, see [Create Recovery Media for Backup](Backup-
    Objects#operation/CreateRecoveryMediaForBackupObject). <p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        id (UUID):
        entity_id (UUID):
        format_ (ERecoveryMediaFormat): Recovery media format.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error]
    """

    kwargs = _get_kwargs(
        id=id,
        entity_id=entity_id,
        format_=format_,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    entity_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    format_: ERecoveryMediaFormat,
    x_api_version: str = "1.3-rev1",
) -> Error | None:
    """Create Recovery Media for Discovered Entity

     The HTTP GET request to the
    `/api/v1/agents/protectionGroups/{id}/discoveredEntities/{entityId}/createRecoveryMedia` endpoint
    creates Veeam Recovery Media for a protected Microsoft Windows computer. The request will create an
    ISO file that you can boot from in case the computer stops working or the hard disk fails.<p>You can
    also create Veeam Recovery Media for a backup created by Veeam Agent for Microsoft Windows. For more
    information, see [Create Recovery Media for Backup](Backup-
    Objects#operation/CreateRecoveryMediaForBackupObject). <p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        id (UUID):
        entity_id (UUID):
        format_ (ERecoveryMediaFormat): Recovery media format.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error
    """

    return (
        await asyncio_detailed(
            id=id,
            entity_id=entity_id,
            client=client,
            format_=format_,
            x_api_version=x_api_version,
        )
    ).parsed

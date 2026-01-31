from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.flr_browse_folder_model import FlrBrowseFolderModel
from ...models.flr_browse_folder_spec import FlrBrowseFolderSpec
from ...types import Response


def _get_kwargs(
    session_id: UUID,
    *,
    body: FlrBrowseFolderSpec,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backupBrowser/flr/{session_id}/browse".format(
            session_id=quote(str(session_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | FlrBrowseFolderModel | None:
    if response.status_code == 200:
        response_200 = FlrBrowseFolderModel.from_dict(response.json())

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
) -> Response[Error | FlrBrowseFolderModel]:
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
    body: FlrBrowseFolderSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | FlrBrowseFolderModel]:
    """Browse File System

     The HTTP POST request to the `/api/v1/backupBrowser/flr/{sessionId}/browse` path allows you to
    browse file system items (drives, folders, files and links) available in a restore session that has
    the specified `sessionId`.<p>You can use this request in the following cases:<li>To browse the file
    system before you restore an item</li><li>To check the item state (changed, not changed, and so on)
    after you have compared the item in the backup and on the production machine</li></p><p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (FlrBrowseFolderSpec): Browser settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | FlrBrowseFolderModel]
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
    body: FlrBrowseFolderSpec,
    x_api_version: str = "1.3-rev0",
) -> Error | FlrBrowseFolderModel | None:
    """Browse File System

     The HTTP POST request to the `/api/v1/backupBrowser/flr/{sessionId}/browse` path allows you to
    browse file system items (drives, folders, files and links) available in a restore session that has
    the specified `sessionId`.<p>You can use this request in the following cases:<li>To browse the file
    system before you restore an item</li><li>To check the item state (changed, not changed, and so on)
    after you have compared the item in the backup and on the production machine</li></p><p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (FlrBrowseFolderSpec): Browser settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | FlrBrowseFolderModel
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
    body: FlrBrowseFolderSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | FlrBrowseFolderModel]:
    """Browse File System

     The HTTP POST request to the `/api/v1/backupBrowser/flr/{sessionId}/browse` path allows you to
    browse file system items (drives, folders, files and links) available in a restore session that has
    the specified `sessionId`.<p>You can use this request in the following cases:<li>To browse the file
    system before you restore an item</li><li>To check the item state (changed, not changed, and so on)
    after you have compared the item in the backup and on the production machine</li></p><p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (FlrBrowseFolderSpec): Browser settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | FlrBrowseFolderModel]
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
    body: FlrBrowseFolderSpec,
    x_api_version: str = "1.3-rev0",
) -> Error | FlrBrowseFolderModel | None:
    """Browse File System

     The HTTP POST request to the `/api/v1/backupBrowser/flr/{sessionId}/browse` path allows you to
    browse file system items (drives, folders, files and links) available in a restore session that has
    the specified `sessionId`.<p>You can use this request in the following cases:<li>To browse the file
    system before you restore an item</li><li>To check the item state (changed, not changed, and so on)
    after you have compared the item in the backup and on the production machine</li></p><p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (FlrBrowseFolderSpec): Browser settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | FlrBrowseFolderModel
    """

    return (
        await asyncio_detailed(
            session_id=session_id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

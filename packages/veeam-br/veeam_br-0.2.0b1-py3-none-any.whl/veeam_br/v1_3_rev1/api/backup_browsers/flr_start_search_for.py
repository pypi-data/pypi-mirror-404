from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.flr_start_search_for_spec import FlrStartSearchForSpec
from ...models.task_model import TaskModel
from ...types import Response


def _get_kwargs(
    session_id: UUID,
    *,
    body: FlrStartSearchForSpec,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backupBrowser/flr/{session_id}/search".format(
            session_id=quote(str(session_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Error | TaskModel | None:
    if response.status_code == 201:
        response_201 = TaskModel.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Error | TaskModel]:
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
    body: FlrStartSearchForSpec,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | TaskModel]:
    """Search for Files and Folders

     The HTTP POST request to the `/api/v1/backupBrowser/flr/{sessionId}/search` endpoint creates a
    search task to find required file system items (drives, folders, files and links) available in a
    restore session that has the specified `sessionId`. <p>To get the search results, run the [Browse
    Search Results](Backup-Browsers#operation/FlrBrowseSearchResult) request. <p>**Available to**&#58;
    Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (FlrStartSearchForSpec): Search files and folders.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | TaskModel]
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
    body: FlrStartSearchForSpec,
    x_api_version: str = "1.3-rev1",
) -> Error | TaskModel | None:
    """Search for Files and Folders

     The HTTP POST request to the `/api/v1/backupBrowser/flr/{sessionId}/search` endpoint creates a
    search task to find required file system items (drives, folders, files and links) available in a
    restore session that has the specified `sessionId`. <p>To get the search results, run the [Browse
    Search Results](Backup-Browsers#operation/FlrBrowseSearchResult) request. <p>**Available to**&#58;
    Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (FlrStartSearchForSpec): Search files and folders.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | TaskModel
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
    body: FlrStartSearchForSpec,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | TaskModel]:
    """Search for Files and Folders

     The HTTP POST request to the `/api/v1/backupBrowser/flr/{sessionId}/search` endpoint creates a
    search task to find required file system items (drives, folders, files and links) available in a
    restore session that has the specified `sessionId`. <p>To get the search results, run the [Browse
    Search Results](Backup-Browsers#operation/FlrBrowseSearchResult) request. <p>**Available to**&#58;
    Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (FlrStartSearchForSpec): Search files and folders.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | TaskModel]
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
    body: FlrStartSearchForSpec,
    x_api_version: str = "1.3-rev1",
) -> Error | TaskModel | None:
    """Search for Files and Folders

     The HTTP POST request to the `/api/v1/backupBrowser/flr/{sessionId}/search` endpoint creates a
    search task to find required file system items (drives, folders, files and links) available in a
    restore session that has the specified `sessionId`. <p>To get the search results, run the [Browse
    Search Results](Backup-Browsers#operation/FlrBrowseSearchResult) request. <p>**Available to**&#58;
    Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (FlrStartSearchForSpec): Search files and folders.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | TaskModel
    """

    return (
        await asyncio_detailed(
            session_id=session_id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

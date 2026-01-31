from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.empty_success_response import EmptySuccessResponse
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: UUID,
    *,
    delete_backups: bool | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    params["deleteBackups"] = delete_backups

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/api/v1/backupInfrastructure/scaleOutRepositories/{id}".format(
            id=quote(str(id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EmptySuccessResponse | Error | None:
    if response.status_code == 204:
        response_204 = EmptySuccessResponse.from_dict(response.json())

        return response_204

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


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[EmptySuccessResponse | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    delete_backups: bool | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[EmptySuccessResponse | Error]:
    """Remove Scale-Out Backup Repository

     The HTTP DELETE request to the `/api/v1/backupInfrastructure/scaleOutRepositories/{id}` path allows
    you to remove a scale-out backup repository that has the specified `id`.<p> **Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        delete_backups (bool | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EmptySuccessResponse | Error]
    """

    kwargs = _get_kwargs(
        id=id,
        delete_backups=delete_backups,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    delete_backups: bool | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> EmptySuccessResponse | Error | None:
    """Remove Scale-Out Backup Repository

     The HTTP DELETE request to the `/api/v1/backupInfrastructure/scaleOutRepositories/{id}` path allows
    you to remove a scale-out backup repository that has the specified `id`.<p> **Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        delete_backups (bool | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EmptySuccessResponse | Error
    """

    return sync_detailed(
        id=id,
        client=client,
        delete_backups=delete_backups,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    delete_backups: bool | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[EmptySuccessResponse | Error]:
    """Remove Scale-Out Backup Repository

     The HTTP DELETE request to the `/api/v1/backupInfrastructure/scaleOutRepositories/{id}` path allows
    you to remove a scale-out backup repository that has the specified `id`.<p> **Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        delete_backups (bool | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EmptySuccessResponse | Error]
    """

    kwargs = _get_kwargs(
        id=id,
        delete_backups=delete_backups,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    delete_backups: bool | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> EmptySuccessResponse | Error | None:
    """Remove Scale-Out Backup Repository

     The HTTP DELETE request to the `/api/v1/backupInfrastructure/scaleOutRepositories/{id}` path allows
    you to remove a scale-out backup repository that has the specified `id`.<p> **Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        delete_backups (bool | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EmptySuccessResponse | Error
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            delete_backups=delete_backups,
            x_api_version=x_api_version,
        )
    ).parsed

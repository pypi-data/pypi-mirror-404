from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.empty_success_response import EmptySuccessResponse
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    mount_id: UUID,
    *,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/restore/instantRecovery/hyperV/vm/{mount_id}/migrate".format(
            mount_id=quote(str(mount_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EmptySuccessResponse | Error | None:
    if response.status_code == 204:
        response_204 = EmptySuccessResponse.from_dict(response.json())

        return response_204

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

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
    mount_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev0",
) -> Response[EmptySuccessResponse | Error]:
    """Start Migrating Microsoft Hyper-V VM

     The HTTP POST request to the `/api/v1/restore/instantRecovery/hyperV/vm/{mountId}/migrate` path
    allows you to start migrating a Microsoft Hyper-V VM for which you have started Instant Recovery,
    using the specified mount point.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EmptySuccessResponse | Error]
    """

    kwargs = _get_kwargs(
        mount_id=mount_id,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    mount_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev0",
) -> EmptySuccessResponse | Error | None:
    """Start Migrating Microsoft Hyper-V VM

     The HTTP POST request to the `/api/v1/restore/instantRecovery/hyperV/vm/{mountId}/migrate` path
    allows you to start migrating a Microsoft Hyper-V VM for which you have started Instant Recovery,
    using the specified mount point.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EmptySuccessResponse | Error
    """

    return sync_detailed(
        mount_id=mount_id,
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    mount_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev0",
) -> Response[EmptySuccessResponse | Error]:
    """Start Migrating Microsoft Hyper-V VM

     The HTTP POST request to the `/api/v1/restore/instantRecovery/hyperV/vm/{mountId}/migrate` path
    allows you to start migrating a Microsoft Hyper-V VM for which you have started Instant Recovery,
    using the specified mount point.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EmptySuccessResponse | Error]
    """

    kwargs = _get_kwargs(
        mount_id=mount_id,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    mount_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev0",
) -> EmptySuccessResponse | Error | None:
    """Start Migrating Microsoft Hyper-V VM

     The HTTP POST request to the `/api/v1/restore/instantRecovery/hyperV/vm/{mountId}/migrate` path
    allows you to start migrating a Microsoft Hyper-V VM for which you have started Instant Recovery,
    using the specified mount point.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EmptySuccessResponse | Error
    """

    return (
        await asyncio_detailed(
            mount_id=mount_id,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed

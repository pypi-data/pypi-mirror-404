from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.hyper_v_volume_manage_model import HyperVVolumeManageModel
from ...types import Response


def _get_kwargs(
    id: UUID,
    *,
    body: HyperVVolumeManageModel,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/api/v1/backupInfrastructure/managedServers/{id}/volumes".format(
            id=quote(str(id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | HyperVVolumeManageModel | None:
    if response.status_code == 200:
        response_200 = HyperVVolumeManageModel.from_dict(response.json())

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
) -> Response[Error | HyperVVolumeManageModel]:
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
    body: HyperVVolumeManageModel,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | HyperVVolumeManageModel]:
    """Edit Volumes on Microsoft Hyper-V Standalone Server

     The HTTP PUT request to the `/api/v1/backupInfrastructure/managedServers/{id}/volumes` endpoint
    edits particular volumes. <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (HyperVVolumeManageModel): Volume properties.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | HyperVVolumeManageModel]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
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
    body: HyperVVolumeManageModel,
    x_api_version: str = "1.3-rev1",
) -> Error | HyperVVolumeManageModel | None:
    """Edit Volumes on Microsoft Hyper-V Standalone Server

     The HTTP PUT request to the `/api/v1/backupInfrastructure/managedServers/{id}/volumes` endpoint
    edits particular volumes. <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (HyperVVolumeManageModel): Volume properties.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | HyperVVolumeManageModel
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: HyperVVolumeManageModel,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | HyperVVolumeManageModel]:
    """Edit Volumes on Microsoft Hyper-V Standalone Server

     The HTTP PUT request to the `/api/v1/backupInfrastructure/managedServers/{id}/volumes` endpoint
    edits particular volumes. <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (HyperVVolumeManageModel): Volume properties.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | HyperVVolumeManageModel]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: HyperVVolumeManageModel,
    x_api_version: str = "1.3-rev1",
) -> Error | HyperVVolumeManageModel | None:
    """Edit Volumes on Microsoft Hyper-V Standalone Server

     The HTTP PUT request to the `/api/v1/backupInfrastructure/managedServers/{id}/volumes` endpoint
    edits particular volumes. <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (HyperVVolumeManageModel): Volume properties.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | HyperVVolumeManageModel
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

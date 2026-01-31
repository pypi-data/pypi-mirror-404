from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.session_model import SessionModel
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: UUID,
    object_id: UUID,
    *,
    from_db_if_sp_unavailable: bool | Unset = UNSET,
    include_gfs: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    params["fromDBIfSPUnavailable"] = from_db_if_sp_unavailable

    params["includeGFS"] = include_gfs

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/api/v1/backups/{id}/objects/{object_id}".format(
            id=quote(str(id), safe=""),
            object_id=quote(str(object_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Error | SessionModel | None:
    if response.status_code == 201:
        response_201 = SessionModel.from_dict(response.json())

        return response_201

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
) -> Response[Error | SessionModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: UUID,
    object_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    from_db_if_sp_unavailable: bool | Unset = UNSET,
    include_gfs: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | SessionModel]:
    """Delete Backup Object

     The HTTP DELETE request to the `/api/v1/backups/{id}/objects/{objectId}` path allows you to delete
    an infrastructure object (VM or VM container) included in a backup that has the specified `id`.
    <p>Types of backup objects differ depending on the backup job platform:<ul> <li>Backups of VMware
    vSphere jobs contain VMs only.</li> <li>Backups of VMware Cloud Director jobs contain VMs and
    vApps.</li></ul></p> <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        object_id (UUID):
        from_db_if_sp_unavailable (bool | Unset):
        include_gfs (bool | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | SessionModel]
    """

    kwargs = _get_kwargs(
        id=id,
        object_id=object_id,
        from_db_if_sp_unavailable=from_db_if_sp_unavailable,
        include_gfs=include_gfs,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: UUID,
    object_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    from_db_if_sp_unavailable: bool | Unset = UNSET,
    include_gfs: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Error | SessionModel | None:
    """Delete Backup Object

     The HTTP DELETE request to the `/api/v1/backups/{id}/objects/{objectId}` path allows you to delete
    an infrastructure object (VM or VM container) included in a backup that has the specified `id`.
    <p>Types of backup objects differ depending on the backup job platform:<ul> <li>Backups of VMware
    vSphere jobs contain VMs only.</li> <li>Backups of VMware Cloud Director jobs contain VMs and
    vApps.</li></ul></p> <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        object_id (UUID):
        from_db_if_sp_unavailable (bool | Unset):
        include_gfs (bool | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | SessionModel
    """

    return sync_detailed(
        id=id,
        object_id=object_id,
        client=client,
        from_db_if_sp_unavailable=from_db_if_sp_unavailable,
        include_gfs=include_gfs,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    object_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    from_db_if_sp_unavailable: bool | Unset = UNSET,
    include_gfs: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | SessionModel]:
    """Delete Backup Object

     The HTTP DELETE request to the `/api/v1/backups/{id}/objects/{objectId}` path allows you to delete
    an infrastructure object (VM or VM container) included in a backup that has the specified `id`.
    <p>Types of backup objects differ depending on the backup job platform:<ul> <li>Backups of VMware
    vSphere jobs contain VMs only.</li> <li>Backups of VMware Cloud Director jobs contain VMs and
    vApps.</li></ul></p> <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        object_id (UUID):
        from_db_if_sp_unavailable (bool | Unset):
        include_gfs (bool | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | SessionModel]
    """

    kwargs = _get_kwargs(
        id=id,
        object_id=object_id,
        from_db_if_sp_unavailable=from_db_if_sp_unavailable,
        include_gfs=include_gfs,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    object_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    from_db_if_sp_unavailable: bool | Unset = UNSET,
    include_gfs: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Error | SessionModel | None:
    """Delete Backup Object

     The HTTP DELETE request to the `/api/v1/backups/{id}/objects/{objectId}` path allows you to delete
    an infrastructure object (VM or VM container) included in a backup that has the specified `id`.
    <p>Types of backup objects differ depending on the backup job platform:<ul> <li>Backups of VMware
    vSphere jobs contain VMs only.</li> <li>Backups of VMware Cloud Director jobs contain VMs and
    vApps.</li></ul></p> <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        object_id (UUID):
        from_db_if_sp_unavailable (bool | Unset):
        include_gfs (bool | Unset):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | SessionModel
    """

    return (
        await asyncio_detailed(
            id=id,
            object_id=object_id,
            client=client,
            from_db_if_sp_unavailable=from_db_if_sp_unavailable,
            include_gfs=include_gfs,
            x_api_version=x_api_version,
        )
    ).parsed

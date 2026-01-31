from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.job_stop_spec import JobStopSpec
from ...models.session_model import SessionModel
from ...types import UNSET, Response, Unset


def _get_kwargs(
    session_id: UUID,
    *,
    body: JobStopSpec | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/restore/entraId/tenant/{session_id}/stop".format(
            session_id=quote(str(session_id), safe=""),
        ),
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

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
    session_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: JobStopSpec | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | SessionModel]:
    """Unmount Microsoft Entra ID Tenant

     The HTTP POST request to the `/api/v1/restore/entraId/tenant/{sessionId}/stop` path allows you to
    unmount a Microsoft Entra ID tenant and stop a mount session that has the specified
    `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (JobStopSpec | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | SessionModel]
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
    body: JobStopSpec | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Error | SessionModel | None:
    """Unmount Microsoft Entra ID Tenant

     The HTTP POST request to the `/api/v1/restore/entraId/tenant/{sessionId}/stop` path allows you to
    unmount a Microsoft Entra ID tenant and stop a mount session that has the specified
    `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (JobStopSpec | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | SessionModel
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
    body: JobStopSpec | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | SessionModel]:
    """Unmount Microsoft Entra ID Tenant

     The HTTP POST request to the `/api/v1/restore/entraId/tenant/{sessionId}/stop` path allows you to
    unmount a Microsoft Entra ID tenant and stop a mount session that has the specified
    `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (JobStopSpec | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | SessionModel]
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
    body: JobStopSpec | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Error | SessionModel | None:
    """Unmount Microsoft Entra ID Tenant

     The HTTP POST request to the `/api/v1/restore/entraId/tenant/{sessionId}/stop` path allows you to
    unmount a Microsoft Entra ID tenant and stop a mount session that has the specified
    `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (JobStopSpec | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | SessionModel
    """

    return (
        await asyncio_detailed(
            session_id=session_id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

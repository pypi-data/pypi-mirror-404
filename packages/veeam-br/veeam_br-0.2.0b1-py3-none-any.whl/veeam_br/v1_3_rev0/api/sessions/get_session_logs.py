from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_task_log_record_status import ETaskLogRecordStatus
from ...models.error import Error
from ...models.session_log_result import SessionLogResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: UUID,
    *,
    status_filter: ETaskLogRecordStatus | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    json_status_filter: str | Unset = UNSET
    if not isinstance(status_filter, Unset):
        json_status_filter = status_filter.value

    params["statusFilter"] = json_status_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/sessions/{id}/logs".format(
            id=quote(str(id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | SessionLogResult | None:
    if response.status_code == 200:
        response_200 = SessionLogResult.from_dict(response.json())

        return response_200

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
) -> Response[Error | SessionLogResult]:
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
    status_filter: ETaskLogRecordStatus | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | SessionLogResult]:
    """Get Session Logs

     The HTTP GET request to the `/api/v1/sessions/{id}/logs` path allows you to get an array of log
    records of a session that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator, Veeam Security Administrator.</p>

    Args:
        id (UUID):
        status_filter (ETaskLogRecordStatus | Unset): Status of the log record.
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | SessionLogResult]
    """

    kwargs = _get_kwargs(
        id=id,
        status_filter=status_filter,
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
    status_filter: ETaskLogRecordStatus | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Error | SessionLogResult | None:
    """Get Session Logs

     The HTTP GET request to the `/api/v1/sessions/{id}/logs` path allows you to get an array of log
    records of a session that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator, Veeam Security Administrator.</p>

    Args:
        id (UUID):
        status_filter (ETaskLogRecordStatus | Unset): Status of the log record.
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | SessionLogResult
    """

    return sync_detailed(
        id=id,
        client=client,
        status_filter=status_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    status_filter: ETaskLogRecordStatus | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | SessionLogResult]:
    """Get Session Logs

     The HTTP GET request to the `/api/v1/sessions/{id}/logs` path allows you to get an array of log
    records of a session that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator, Veeam Security Administrator.</p>

    Args:
        id (UUID):
        status_filter (ETaskLogRecordStatus | Unset): Status of the log record.
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | SessionLogResult]
    """

    kwargs = _get_kwargs(
        id=id,
        status_filter=status_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    status_filter: ETaskLogRecordStatus | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Error | SessionLogResult | None:
    """Get Session Logs

     The HTTP GET request to the `/api/v1/sessions/{id}/logs` path allows you to get an array of log
    records of a session that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator, Veeam Security Administrator.</p>

    Args:
        id (UUID):
        status_filter (ETaskLogRecordStatus | Unset): Status of the log record.
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | SessionLogResult
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            status_filter=status_filter,
            x_api_version=x_api_version,
        )
    ).parsed

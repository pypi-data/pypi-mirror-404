from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.general_options_notifications_model import GeneralOptionsNotificationsModel
from ...types import Response


def _get_kwargs(
    *,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/generalOptions/notifications",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | GeneralOptionsNotificationsModel | None:
    if response.status_code == 200:
        response_200 = GeneralOptionsNotificationsModel.from_dict(response.json())

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
) -> Response[Error | GeneralOptionsNotificationsModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | GeneralOptionsNotificationsModel]:
    """Get Notification Settings

     The HTTP GET request to the `/api/v1/generalOptions/notifications` endpoint gets Veeam Backup &
    Replication notifications settings.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | GeneralOptionsNotificationsModel]
    """

    kwargs = _get_kwargs(
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev1",
) -> Error | GeneralOptionsNotificationsModel | None:
    """Get Notification Settings

     The HTTP GET request to the `/api/v1/generalOptions/notifications` endpoint gets Veeam Backup &
    Replication notifications settings.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | GeneralOptionsNotificationsModel
    """

    return sync_detailed(
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | GeneralOptionsNotificationsModel]:
    """Get Notification Settings

     The HTTP GET request to the `/api/v1/generalOptions/notifications` endpoint gets Veeam Backup &
    Replication notifications settings.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | GeneralOptionsNotificationsModel]
    """

    kwargs = _get_kwargs(
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev1",
) -> Error | GeneralOptionsNotificationsModel | None:
    """Get Notification Settings

     The HTTP GET request to the `/api/v1/generalOptions/notifications` endpoint gets Veeam Backup &
    Replication notifications settings.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | GeneralOptionsNotificationsModel
    """

    return (
        await asyncio_detailed(
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed

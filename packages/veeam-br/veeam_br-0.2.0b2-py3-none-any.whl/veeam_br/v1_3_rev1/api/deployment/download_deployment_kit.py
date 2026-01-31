from http import HTTPStatus
from io import BytesIO
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...types import File, Response


def _get_kwargs(
    task_id: UUID,
    *,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/deployment/{task_id}/downloadKit".format(
            task_id=quote(str(task_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Error | File | None:
    if response.status_code == 200:
        response_200 = File(payload=BytesIO(response.content))

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Error | File]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    task_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | File]:
    """Download Deployment Kit Package

     The HTTP GET request to the `/api/v1/deployment/{taskId}/downloadKit` endpoint downloads the
    deployment kit as a ZIP file. Save the ZIP file to the Microsoft Windows server you want to add as a
    managed server, extract its contents and run the `InstalDeploymentKit.bat` configuration script to
    install the required packages and certificates. <p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        task_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | File]
    """

    kwargs = _get_kwargs(
        task_id=task_id,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    task_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev1",
) -> Error | File | None:
    """Download Deployment Kit Package

     The HTTP GET request to the `/api/v1/deployment/{taskId}/downloadKit` endpoint downloads the
    deployment kit as a ZIP file. Save the ZIP file to the Microsoft Windows server you want to add as a
    managed server, extract its contents and run the `InstalDeploymentKit.bat` configuration script to
    install the required packages and certificates. <p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        task_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | File
    """

    return sync_detailed(
        task_id=task_id,
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    task_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | File]:
    """Download Deployment Kit Package

     The HTTP GET request to the `/api/v1/deployment/{taskId}/downloadKit` endpoint downloads the
    deployment kit as a ZIP file. Save the ZIP file to the Microsoft Windows server you want to add as a
    managed server, extract its contents and run the `InstalDeploymentKit.bat` configuration script to
    install the required packages and certificates. <p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        task_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | File]
    """

    kwargs = _get_kwargs(
        task_id=task_id,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    task_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev1",
) -> Error | File | None:
    """Download Deployment Kit Package

     The HTTP GET request to the `/api/v1/deployment/{taskId}/downloadKit` endpoint downloads the
    deployment kit as a ZIP file. Save the ZIP file to the Microsoft Windows server you want to add as a
    managed server, extract its contents and run the `InstalDeploymentKit.bat` configuration script to
    install the required packages and certificates. <p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        task_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | File
    """

    return (
        await asyncio_detailed(
            task_id=task_id,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed

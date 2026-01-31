from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.cloud_native_application_model import CloudNativeApplicationModel
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    verification_code: str,
    *,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/cloudCredentials/appRegistration/{verification_code}".format(
            verification_code=quote(str(verification_code), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CloudNativeApplicationModel | Error | None:
    if response.status_code == 201:
        response_201 = CloudNativeApplicationModel.from_dict(response.json())

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


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[CloudNativeApplicationModel | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    verification_code: str,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.2-rev1",
) -> Response[CloudNativeApplicationModel | Error]:
    """Register Microsoft Entra ID Application

     The HTTP POST request to the `/api/v1/cloudCredentials/appRegistration/{verificationCode}` path
    allows you to register a new Microsoft Entra ID application using the specified
    `verificationCode`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        verification_code (str):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CloudNativeApplicationModel | Error]
    """

    kwargs = _get_kwargs(
        verification_code=verification_code,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    verification_code: str,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.2-rev1",
) -> CloudNativeApplicationModel | Error | None:
    """Register Microsoft Entra ID Application

     The HTTP POST request to the `/api/v1/cloudCredentials/appRegistration/{verificationCode}` path
    allows you to register a new Microsoft Entra ID application using the specified
    `verificationCode`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        verification_code (str):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CloudNativeApplicationModel | Error
    """

    return sync_detailed(
        verification_code=verification_code,
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    verification_code: str,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.2-rev1",
) -> Response[CloudNativeApplicationModel | Error]:
    """Register Microsoft Entra ID Application

     The HTTP POST request to the `/api/v1/cloudCredentials/appRegistration/{verificationCode}` path
    allows you to register a new Microsoft Entra ID application using the specified
    `verificationCode`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        verification_code (str):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CloudNativeApplicationModel | Error]
    """

    kwargs = _get_kwargs(
        verification_code=verification_code,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    verification_code: str,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.2-rev1",
) -> CloudNativeApplicationModel | Error | None:
    """Register Microsoft Entra ID Application

     The HTTP POST request to the `/api/v1/cloudCredentials/appRegistration/{verificationCode}` path
    allows you to register a new Microsoft Entra ID application using the specified
    `verificationCode`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        verification_code (str):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CloudNativeApplicationModel | Error
    """

    return (
        await asyncio_detailed(
            verification_code=verification_code,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed

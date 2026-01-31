from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.cloud_credentials_model import CloudCredentialsModel
from ...models.cloud_credentials_password_spec import CloudCredentialsPasswordSpec
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    id: UUID,
    *,
    body: CloudCredentialsPasswordSpec,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/cloudCredentials/{id}/changeSecretKey".format(
            id=quote(str(id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CloudCredentialsModel | Error | None:
    if response.status_code == 201:
        response_201 = CloudCredentialsModel.from_dict(response.json())

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
) -> Response[CloudCredentialsModel | Error]:
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
    body: CloudCredentialsPasswordSpec,
    x_api_version: str = "1.2-rev1",
) -> Response[CloudCredentialsModel | Error]:
    """Change Secret Key

     The HTTP POST request to the `/api/v1/cloudCredentials/{id}/changeSecretKey` path allows you to
    change a secret key of a cloud credentials record that has the specified `id`.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Security Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (CloudCredentialsPasswordSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CloudCredentialsModel | Error]
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
    body: CloudCredentialsPasswordSpec,
    x_api_version: str = "1.2-rev1",
) -> CloudCredentialsModel | Error | None:
    """Change Secret Key

     The HTTP POST request to the `/api/v1/cloudCredentials/{id}/changeSecretKey` path allows you to
    change a secret key of a cloud credentials record that has the specified `id`.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Security Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (CloudCredentialsPasswordSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CloudCredentialsModel | Error
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
    body: CloudCredentialsPasswordSpec,
    x_api_version: str = "1.2-rev1",
) -> Response[CloudCredentialsModel | Error]:
    """Change Secret Key

     The HTTP POST request to the `/api/v1/cloudCredentials/{id}/changeSecretKey` path allows you to
    change a secret key of a cloud credentials record that has the specified `id`.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Security Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (CloudCredentialsPasswordSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CloudCredentialsModel | Error]
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
    body: CloudCredentialsPasswordSpec,
    x_api_version: str = "1.2-rev1",
) -> CloudCredentialsModel | Error | None:
    """Change Secret Key

     The HTTP POST request to the `/api/v1/cloudCredentials/{id}/changeSecretKey` path allows you to
    change a secret key of a cloud credentials record that has the specified `id`.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Security Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (CloudCredentialsPasswordSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CloudCredentialsModel | Error
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

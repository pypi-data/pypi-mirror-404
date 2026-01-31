from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.credentials_model import CredentialsModel
from ...models.credentials_spec import CredentialsSpec
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    *,
    body: CredentialsSpec,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/credentials",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CredentialsModel | Error | None:
    if response.status_code == 201:
        response_201 = CredentialsModel.from_dict(response.json())

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
) -> Response[CredentialsModel | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CredentialsSpec,
    x_api_version: str = "1.2-rev1",
) -> Response[CredentialsModel | Error]:
    """Add Credentials Record

     The HTTP POST request to the `/api/v1/credentials` path allows you to add a credentials
    record.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (CredentialsSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CredentialsModel | Error]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: CredentialsSpec,
    x_api_version: str = "1.2-rev1",
) -> CredentialsModel | Error | None:
    """Add Credentials Record

     The HTTP POST request to the `/api/v1/credentials` path allows you to add a credentials
    record.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (CredentialsSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CredentialsModel | Error
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CredentialsSpec,
    x_api_version: str = "1.2-rev1",
) -> Response[CredentialsModel | Error]:
    """Add Credentials Record

     The HTTP POST request to the `/api/v1/credentials` path allows you to add a credentials
    record.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (CredentialsSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CredentialsModel | Error]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CredentialsSpec,
    x_api_version: str = "1.2-rev1",
) -> CredentialsModel | Error | None:
    """Add Credentials Record

     The HTTP POST request to the `/api/v1/credentials` path allows you to add a credentials
    record.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (CredentialsSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CredentialsModel | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

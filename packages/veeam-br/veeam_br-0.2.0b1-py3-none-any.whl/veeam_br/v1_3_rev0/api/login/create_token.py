from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.token_login_spec import TokenLoginSpec
from ...models.token_model import TokenModel
from ...types import Response


def _get_kwargs(
    *,
    body: TokenLoginSpec,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/oauth2/token",
    }

    _kwargs["data"] = body.to_dict()

    headers["Content-Type"] = "application/x-www-form-urlencoded"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Error | TokenModel | None:
    if response.status_code == 200:
        response_200 = TokenModel.from_dict(response.json())

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

    if response.status_code == 500:
        response_500 = Error.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Error | TokenModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TokenLoginSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | TokenModel]:
    """Get Access Token

     The HTTP POST request to the `/api/oauth2/token` path allows you to get an access token and a
    refresh token.<p>**Available to**&#58; All built-in user roles. Authentication with custom roles is
    not allowed.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (TokenLoginSpec): Authentication settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | TokenModel]
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
    body: TokenLoginSpec,
    x_api_version: str = "1.3-rev0",
) -> Error | TokenModel | None:
    """Get Access Token

     The HTTP POST request to the `/api/oauth2/token` path allows you to get an access token and a
    refresh token.<p>**Available to**&#58; All built-in user roles. Authentication with custom roles is
    not allowed.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (TokenLoginSpec): Authentication settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | TokenModel
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TokenLoginSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | TokenModel]:
    """Get Access Token

     The HTTP POST request to the `/api/oauth2/token` path allows you to get an access token and a
    refresh token.<p>**Available to**&#58; All built-in user roles. Authentication with custom roles is
    not allowed.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (TokenLoginSpec): Authentication settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | TokenModel]
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
    body: TokenLoginSpec,
    x_api_version: str = "1.3-rev0",
) -> Error | TokenModel | None:
    """Get Access Token

     The HTTP POST request to the `/api/oauth2/token` path allows you to get an access token and a
    refresh token.<p>**Available to**&#58; All built-in user roles. Authentication with custom roles is
    not allowed.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (TokenLoginSpec): Authentication settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | TokenModel
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

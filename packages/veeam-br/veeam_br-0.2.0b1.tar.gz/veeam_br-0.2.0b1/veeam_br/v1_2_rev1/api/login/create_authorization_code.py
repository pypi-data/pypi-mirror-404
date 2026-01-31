from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.authorization_code_model import AuthorizationCodeModel
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    *,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/oauth2/authorization_code",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AuthorizationCodeModel | Error | None:
    if response.status_code == 200:
        response_200 = AuthorizationCodeModel.from_dict(response.json())

        return response_200

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
) -> Response[AuthorizationCodeModel | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.2-rev1",
) -> Response[AuthorizationCodeModel | Error]:
    """Get Authorization Code

     The HTTP POST request to the `/api/oauth2/authorization_code` path allows you to get an
    authorization code that is used to obtain an access token. For more information on authorization
    process, see [Requesting Authorization](https://helpcenter.veeam.com/docs/backup/vbr_rest/requesting
    _authorization.html?ver=120). <p>**Available to**&#58; All user roles.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthorizationCodeModel | Error]
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
    x_api_version: str = "1.2-rev1",
) -> AuthorizationCodeModel | Error | None:
    """Get Authorization Code

     The HTTP POST request to the `/api/oauth2/authorization_code` path allows you to get an
    authorization code that is used to obtain an access token. For more information on authorization
    process, see [Requesting Authorization](https://helpcenter.veeam.com/docs/backup/vbr_rest/requesting
    _authorization.html?ver=120). <p>**Available to**&#58; All user roles.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthorizationCodeModel | Error
    """

    return sync_detailed(
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.2-rev1",
) -> Response[AuthorizationCodeModel | Error]:
    """Get Authorization Code

     The HTTP POST request to the `/api/oauth2/authorization_code` path allows you to get an
    authorization code that is used to obtain an access token. For more information on authorization
    process, see [Requesting Authorization](https://helpcenter.veeam.com/docs/backup/vbr_rest/requesting
    _authorization.html?ver=120). <p>**Available to**&#58; All user roles.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthorizationCodeModel | Error]
    """

    kwargs = _get_kwargs(
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.2-rev1",
) -> AuthorizationCodeModel | Error | None:
    """Get Authorization Code

     The HTTP POST request to the `/api/oauth2/authorization_code` path allows you to get an
    authorization code that is used to obtain an access token. For more information on authorization
    process, see [Requesting Authorization](https://helpcenter.veeam.com/docs/backup/vbr_rest/requesting
    _authorization.html?ver=120). <p>**Available to**&#58; All user roles.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthorizationCodeModel | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed

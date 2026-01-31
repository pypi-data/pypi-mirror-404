from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.ad_domain_model import ADDomainModel
from ...models.ad_domain_spec import ADDomainSpec
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    *,
    body: ADDomainSpec,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/adDomains",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> ADDomainModel | Error | None:
    if response.status_code == 201:
        response_201 = ADDomainModel.from_dict(response.json())

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
) -> Response[ADDomainModel | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ADDomainSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[ADDomainModel | Error]:
    """Add Active Directory Domain

     The HTTP POST request to the `/api/v1/adDomains` path allows you to add an Active Directory domain
    to the backup server. <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (ADDomainSpec): Settings of Active Directory domain.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ADDomainModel | Error]
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
    body: ADDomainSpec,
    x_api_version: str = "1.3-rev0",
) -> ADDomainModel | Error | None:
    """Add Active Directory Domain

     The HTTP POST request to the `/api/v1/adDomains` path allows you to add an Active Directory domain
    to the backup server. <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (ADDomainSpec): Settings of Active Directory domain.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ADDomainModel | Error
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ADDomainSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[ADDomainModel | Error]:
    """Add Active Directory Domain

     The HTTP POST request to the `/api/v1/adDomains` path allows you to add an Active Directory domain
    to the backup server. <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (ADDomainSpec): Settings of Active Directory domain.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ADDomainModel | Error]
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
    body: ADDomainSpec,
    x_api_version: str = "1.3-rev0",
) -> ADDomainModel | Error | None:
    """Add Active Directory Domain

     The HTTP POST request to the `/api/v1/adDomains` path allows you to add an Active Directory domain
    to the backup server. <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (ADDomainSpec): Settings of Active Directory domain.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ADDomainModel | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

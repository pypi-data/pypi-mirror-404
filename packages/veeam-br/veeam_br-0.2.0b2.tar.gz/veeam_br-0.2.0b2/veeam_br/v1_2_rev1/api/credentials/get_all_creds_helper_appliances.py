from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.cloud_helper_appliance_result import CloudHelperApplianceResult
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    id: UUID,
    *,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/cloudCredentials/{id}/helperAppliances".format(
            id=quote(str(id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CloudHelperApplianceResult | Error | None:
    if response.status_code == 200:
        response_200 = CloudHelperApplianceResult.from_dict(response.json())

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


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[CloudHelperApplianceResult | Error]:
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
    x_api_version: str = "1.2-rev1",
) -> Response[CloudHelperApplianceResult | Error]:
    """Get All Helper Appliances

     The HTTP GET request to the `/api/v1/cloudCredentials/{id}/helperAppliances` path allows you to get
    an array of Linux-based helper appliances of a Microsoft Azure compute account that has the
    specified `id`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CloudHelperApplianceResult | Error]
    """

    kwargs = _get_kwargs(
        id=id,
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
    x_api_version: str = "1.2-rev1",
) -> CloudHelperApplianceResult | Error | None:
    """Get All Helper Appliances

     The HTTP GET request to the `/api/v1/cloudCredentials/{id}/helperAppliances` path allows you to get
    an array of Linux-based helper appliances of a Microsoft Azure compute account that has the
    specified `id`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CloudHelperApplianceResult | Error
    """

    return sync_detailed(
        id=id,
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.2-rev1",
) -> Response[CloudHelperApplianceResult | Error]:
    """Get All Helper Appliances

     The HTTP GET request to the `/api/v1/cloudCredentials/{id}/helperAppliances` path allows you to get
    an array of Linux-based helper appliances of a Microsoft Azure compute account that has the
    specified `id`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CloudHelperApplianceResult | Error]
    """

    kwargs = _get_kwargs(
        id=id,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.2-rev1",
) -> CloudHelperApplianceResult | Error | None:
    """Get All Helper Appliances

     The HTTP GET request to the `/api/v1/cloudCredentials/{id}/helperAppliances` path allows you to get
    an array of Linux-based helper appliances of a Microsoft Azure compute account that has the
    specified `id`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CloudHelperApplianceResult | Error
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed

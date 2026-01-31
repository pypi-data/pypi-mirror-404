from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.cloud_browser_model import CloudBrowserModel
from ...models.cloud_browser_spec import CloudBrowserSpec
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: CloudBrowserSpec,
    reset_cache: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    params["resetCache"] = reset_cache

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/cloudBrowser",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CloudBrowserModel | Error | None:
    if response.status_code == 200:
        response_200 = CloudBrowserModel.from_dict(response.json())

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
) -> Response[CloudBrowserModel | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CloudBrowserSpec,
    reset_cache: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[CloudBrowserModel | Error]:
    """Get Cloud Hierarchy

     The HTTP POST request to the `/api/v1/cloudBrowser` endpoint browses cloud resources (compute or
    storage) available for the specified storage account.<p>To reduce the response time and the number
    of records in the response, use `filters` if possible.</p><p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        reset_cache (bool | Unset):
        x_api_version (str):  Default: '1.3-rev1'.
        body (CloudBrowserSpec): Cloud resource settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CloudBrowserModel | Error]
    """

    kwargs = _get_kwargs(
        body=body,
        reset_cache=reset_cache,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: CloudBrowserSpec,
    reset_cache: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> CloudBrowserModel | Error | None:
    """Get Cloud Hierarchy

     The HTTP POST request to the `/api/v1/cloudBrowser` endpoint browses cloud resources (compute or
    storage) available for the specified storage account.<p>To reduce the response time and the number
    of records in the response, use `filters` if possible.</p><p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        reset_cache (bool | Unset):
        x_api_version (str):  Default: '1.3-rev1'.
        body (CloudBrowserSpec): Cloud resource settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CloudBrowserModel | Error
    """

    return sync_detailed(
        client=client,
        body=body,
        reset_cache=reset_cache,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CloudBrowserSpec,
    reset_cache: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[CloudBrowserModel | Error]:
    """Get Cloud Hierarchy

     The HTTP POST request to the `/api/v1/cloudBrowser` endpoint browses cloud resources (compute or
    storage) available for the specified storage account.<p>To reduce the response time and the number
    of records in the response, use `filters` if possible.</p><p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        reset_cache (bool | Unset):
        x_api_version (str):  Default: '1.3-rev1'.
        body (CloudBrowserSpec): Cloud resource settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CloudBrowserModel | Error]
    """

    kwargs = _get_kwargs(
        body=body,
        reset_cache=reset_cache,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CloudBrowserSpec,
    reset_cache: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> CloudBrowserModel | Error | None:
    """Get Cloud Hierarchy

     The HTTP POST request to the `/api/v1/cloudBrowser` endpoint browses cloud resources (compute or
    storage) available for the specified storage account.<p>To reduce the response time and the number
    of records in the response, use `filters` if possible.</p><p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        reset_cache (bool | Unset):
        x_api_version (str):  Default: '1.3-rev1'.
        body (CloudBrowserSpec): Cloud resource settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CloudBrowserModel | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            reset_cache=reset_cache,
            x_api_version=x_api_version,
        )
    ).parsed

from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.cloud_browser_model import CloudBrowserModel
from ...models.error import Error
from ...models.veeam_data_cloud_vault_storage_browser_spec import VeeamDataCloudVaultStorageBrowserSpec
from ...types import UNSET, Response, Unset


def _get_kwargs(
    vault_id: str,
    *,
    body: VeeamDataCloudVaultStorageBrowserSpec,
    reset_cache: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    params["resetCache"] = reset_cache

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/cloudBrowser/{vault_id}".format(
            vault_id=quote(str(vault_id), safe=""),
        ),
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
    vault_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: VeeamDataCloudVaultStorageBrowserSpec,
    reset_cache: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[CloudBrowserModel | Error]:
    """Browse Veeam Data Cloud Vault

     The HTTP POST request to the `/api/v1/cloudBrowser/{vaultId}` path allows you to browse cloud
    storage resources available for the Veeam Data Cloud Vault.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        vault_id (str):
        reset_cache (bool | Unset):
        x_api_version (str):  Default: '1.3-rev0'.
        body (VeeamDataCloudVaultStorageBrowserSpec): Settings for Veeam Data Cloud Vault.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CloudBrowserModel | Error]
    """

    kwargs = _get_kwargs(
        vault_id=vault_id,
        body=body,
        reset_cache=reset_cache,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    vault_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: VeeamDataCloudVaultStorageBrowserSpec,
    reset_cache: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> CloudBrowserModel | Error | None:
    """Browse Veeam Data Cloud Vault

     The HTTP POST request to the `/api/v1/cloudBrowser/{vaultId}` path allows you to browse cloud
    storage resources available for the Veeam Data Cloud Vault.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        vault_id (str):
        reset_cache (bool | Unset):
        x_api_version (str):  Default: '1.3-rev0'.
        body (VeeamDataCloudVaultStorageBrowserSpec): Settings for Veeam Data Cloud Vault.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CloudBrowserModel | Error
    """

    return sync_detailed(
        vault_id=vault_id,
        client=client,
        body=body,
        reset_cache=reset_cache,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    vault_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: VeeamDataCloudVaultStorageBrowserSpec,
    reset_cache: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[CloudBrowserModel | Error]:
    """Browse Veeam Data Cloud Vault

     The HTTP POST request to the `/api/v1/cloudBrowser/{vaultId}` path allows you to browse cloud
    storage resources available for the Veeam Data Cloud Vault.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        vault_id (str):
        reset_cache (bool | Unset):
        x_api_version (str):  Default: '1.3-rev0'.
        body (VeeamDataCloudVaultStorageBrowserSpec): Settings for Veeam Data Cloud Vault.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CloudBrowserModel | Error]
    """

    kwargs = _get_kwargs(
        vault_id=vault_id,
        body=body,
        reset_cache=reset_cache,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    vault_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: VeeamDataCloudVaultStorageBrowserSpec,
    reset_cache: bool | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> CloudBrowserModel | Error | None:
    """Browse Veeam Data Cloud Vault

     The HTTP POST request to the `/api/v1/cloudBrowser/{vaultId}` path allows you to browse cloud
    storage resources available for the Veeam Data Cloud Vault.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        vault_id (str):
        reset_cache (bool | Unset):
        x_api_version (str):  Default: '1.3-rev0'.
        body (VeeamDataCloudVaultStorageBrowserSpec): Settings for Veeam Data Cloud Vault.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CloudBrowserModel | Error
    """

    return (
        await asyncio_detailed(
            vault_id=vault_id,
            client=client,
            body=body,
            reset_cache=reset_cache,
            x_api_version=x_api_version,
        )
    ).parsed

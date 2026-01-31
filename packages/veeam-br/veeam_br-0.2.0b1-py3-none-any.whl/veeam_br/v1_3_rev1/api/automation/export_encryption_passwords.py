from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.encryption_password_export_spec import EncryptionPasswordExportSpec
from ...models.encryption_password_import_spec_collection import EncryptionPasswordImportSpecCollection
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: EncryptionPasswordExportSpec | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/automation/encryptionPasswords/export",
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EncryptionPasswordImportSpecCollection | Error | None:
    if response.status_code == 200:
        response_200 = EncryptionPasswordImportSpecCollection.from_dict(response.json())

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
) -> Response[EncryptionPasswordImportSpecCollection | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: EncryptionPasswordExportSpec | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[EncryptionPasswordImportSpecCollection | Error]:
    """Export Encryption Passwords

     The HTTP POST request to the `/api/v1/automation/encryptionPasswords/export` endpoint exports
    encryption passwords from Veeam Backup & Replication.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (EncryptionPasswordExportSpec | Unset): Export settings for data encryption
            passwords.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EncryptionPasswordImportSpecCollection | Error]
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
    body: EncryptionPasswordExportSpec | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> EncryptionPasswordImportSpecCollection | Error | None:
    """Export Encryption Passwords

     The HTTP POST request to the `/api/v1/automation/encryptionPasswords/export` endpoint exports
    encryption passwords from Veeam Backup & Replication.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (EncryptionPasswordExportSpec | Unset): Export settings for data encryption
            passwords.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EncryptionPasswordImportSpecCollection | Error
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: EncryptionPasswordExportSpec | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[EncryptionPasswordImportSpecCollection | Error]:
    """Export Encryption Passwords

     The HTTP POST request to the `/api/v1/automation/encryptionPasswords/export` endpoint exports
    encryption passwords from Veeam Backup & Replication.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (EncryptionPasswordExportSpec | Unset): Export settings for data encryption
            passwords.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EncryptionPasswordImportSpecCollection | Error]
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
    body: EncryptionPasswordExportSpec | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> EncryptionPasswordImportSpecCollection | Error | None:
    """Export Encryption Passwords

     The HTTP POST request to the `/api/v1/automation/encryptionPasswords/export` endpoint exports
    encryption passwords from Veeam Backup & Replication.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (EncryptionPasswordExportSpec | Unset): Export settings for data encryption
            passwords.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EncryptionPasswordImportSpecCollection | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

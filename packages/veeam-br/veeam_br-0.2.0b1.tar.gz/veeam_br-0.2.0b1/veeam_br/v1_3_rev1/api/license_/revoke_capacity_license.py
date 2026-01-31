from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.capacity_license_workload_model import CapacityLicenseWorkloadModel
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    instance_id: UUID,
    *,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/license/capacity/{instance_id}/revoke".format(
            instance_id=quote(str(instance_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CapacityLicenseWorkloadModel | Error | None:
    if response.status_code == 200:
        response_200 = CapacityLicenseWorkloadModel.from_dict(response.json())

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
) -> Response[CapacityLicenseWorkloadModel | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    instance_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev1",
) -> Response[CapacityLicenseWorkloadModel | Error]:
    """Revoke Capacity License From Unstructured Data Workload

     The HTTP POST request to the `/api/v1/license/capacity/{instanceId}/revoke` endpoint revokes a
    capacity instance with the specified `instanceId` from an unstructured data workload (file share or
    object storage). <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        instance_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CapacityLicenseWorkloadModel | Error]
    """

    kwargs = _get_kwargs(
        instance_id=instance_id,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    instance_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev1",
) -> CapacityLicenseWorkloadModel | Error | None:
    """Revoke Capacity License From Unstructured Data Workload

     The HTTP POST request to the `/api/v1/license/capacity/{instanceId}/revoke` endpoint revokes a
    capacity instance with the specified `instanceId` from an unstructured data workload (file share or
    object storage). <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        instance_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CapacityLicenseWorkloadModel | Error
    """

    return sync_detailed(
        instance_id=instance_id,
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    instance_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev1",
) -> Response[CapacityLicenseWorkloadModel | Error]:
    """Revoke Capacity License From Unstructured Data Workload

     The HTTP POST request to the `/api/v1/license/capacity/{instanceId}/revoke` endpoint revokes a
    capacity instance with the specified `instanceId` from an unstructured data workload (file share or
    object storage). <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        instance_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CapacityLicenseWorkloadModel | Error]
    """

    kwargs = _get_kwargs(
        instance_id=instance_id,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    instance_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    x_api_version: str = "1.3-rev1",
) -> CapacityLicenseWorkloadModel | Error | None:
    """Revoke Capacity License From Unstructured Data Workload

     The HTTP POST request to the `/api/v1/license/capacity/{instanceId}/revoke` endpoint revokes a
    capacity instance with the specified `instanceId` from an unstructured data workload (file share or
    object storage). <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        instance_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CapacityLicenseWorkloadModel | Error
    """

    return (
        await asyncio_detailed(
            instance_id=instance_id,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed

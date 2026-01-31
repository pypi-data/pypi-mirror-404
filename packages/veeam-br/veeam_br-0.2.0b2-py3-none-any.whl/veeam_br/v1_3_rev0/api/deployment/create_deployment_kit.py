from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_deployment_kit_spec import CreateDeploymentKitSpec
from ...models.error import Error
from ...models.task_model import TaskModel
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: CreateDeploymentKitSpec | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/deployment/generateKit",
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Error | TaskModel | None:
    if response.status_code == 201:
        response_201 = TaskModel.from_dict(response.json())

        return response_201

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Error | TaskModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateDeploymentKitSpec | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | TaskModel]:
    """Create Deployment Kit

     The HTTP POST request to the `/api/v1/deployment/generateKit` path allows you to generate a
    deployment kit which can be used for adding Windows machines as managed servers.<p>**Available
    to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (CreateDeploymentKitSpec | Unset): Deployment kit settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | TaskModel]
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
    body: CreateDeploymentKitSpec | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Error | TaskModel | None:
    """Create Deployment Kit

     The HTTP POST request to the `/api/v1/deployment/generateKit` path allows you to generate a
    deployment kit which can be used for adding Windows machines as managed servers.<p>**Available
    to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (CreateDeploymentKitSpec | Unset): Deployment kit settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | TaskModel
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateDeploymentKitSpec | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Error | TaskModel]:
    """Create Deployment Kit

     The HTTP POST request to the `/api/v1/deployment/generateKit` path allows you to generate a
    deployment kit which can be used for adding Windows machines as managed servers.<p>**Available
    to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (CreateDeploymentKitSpec | Unset): Deployment kit settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | TaskModel]
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
    body: CreateDeploymentKitSpec | Unset = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Error | TaskModel | None:
    """Create Deployment Kit

     The HTTP POST request to the `/api/v1/deployment/generateKit` path allows you to generate a
    deployment kit which can be used for adding Windows machines as managed servers.<p>**Available
    to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (CreateDeploymentKitSpec | Unset): Deployment kit settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | TaskModel
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

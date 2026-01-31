from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.flr_search_for_result_model import FlrSearchForResultModel
from ...models.flr_search_for_result_spec import FlrSearchForResultSpec
from ...types import Response


def _get_kwargs(
    session_id: UUID,
    task_id: UUID,
    *,
    body: FlrSearchForResultSpec,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backupBrowser/flr/unstructuredData/{session_id}/search/{task_id}/browse".format(
            session_id=quote(str(session_id), safe=""),
            task_id=quote(str(task_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | FlrSearchForResultModel | None:
    if response.status_code == 200:
        response_200 = FlrSearchForResultModel.from_dict(response.json())

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
) -> Response[Error | FlrSearchForResultModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    session_id: UUID,
    task_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: FlrSearchForResultSpec,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | FlrSearchForResultModel]:
    """Browse Search Results

     The HTTP POST request to the
    `/api/v1/backupBrowser/flr/unstructuredData/{sessionId}/search/{taskId}/browse` path allows you to
    browse search results of a search task that has the specified `taskId`. <p>**Available to**&#58;
    Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        task_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (FlrSearchForResultSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | FlrSearchForResultModel]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        task_id=task_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    session_id: UUID,
    task_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: FlrSearchForResultSpec,
    x_api_version: str = "1.2-rev1",
) -> Error | FlrSearchForResultModel | None:
    """Browse Search Results

     The HTTP POST request to the
    `/api/v1/backupBrowser/flr/unstructuredData/{sessionId}/search/{taskId}/browse` path allows you to
    browse search results of a search task that has the specified `taskId`. <p>**Available to**&#58;
    Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        task_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (FlrSearchForResultSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | FlrSearchForResultModel
    """

    return sync_detailed(
        session_id=session_id,
        task_id=task_id,
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    session_id: UUID,
    task_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: FlrSearchForResultSpec,
    x_api_version: str = "1.2-rev1",
) -> Response[Error | FlrSearchForResultModel]:
    """Browse Search Results

     The HTTP POST request to the
    `/api/v1/backupBrowser/flr/unstructuredData/{sessionId}/search/{taskId}/browse` path allows you to
    browse search results of a search task that has the specified `taskId`. <p>**Available to**&#58;
    Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        task_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (FlrSearchForResultSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | FlrSearchForResultModel]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        task_id=task_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    session_id: UUID,
    task_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: FlrSearchForResultSpec,
    x_api_version: str = "1.2-rev1",
) -> Error | FlrSearchForResultModel | None:
    """Browse Search Results

     The HTTP POST request to the
    `/api/v1/backupBrowser/flr/unstructuredData/{sessionId}/search/{taskId}/browse` path allows you to
    browse search results of a search task that has the specified `taskId`. <p>**Available to**&#58;
    Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        task_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (FlrSearchForResultSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | FlrSearchForResultModel
    """

    return (
        await asyncio_detailed(
            session_id=session_id,
            task_id=task_id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

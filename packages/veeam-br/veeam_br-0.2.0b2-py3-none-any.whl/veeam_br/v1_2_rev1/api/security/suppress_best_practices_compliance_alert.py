from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.best_practices_compliance_model import BestPracticesComplianceModel
from ...models.best_practices_suppress_request import BestPracticesSuppressRequest
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: UUID,
    *,
    body: BestPracticesSuppressRequest | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/securityAnalyzer/bestPractices/{id}/suppress".format(
            id=quote(str(id), safe=""),
        ),
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BestPracticesComplianceModel | Error | None:
    if response.status_code == 200:
        response_200 = BestPracticesComplianceModel.from_dict(response.json())

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
) -> Response[BestPracticesComplianceModel | Error]:
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
    body: BestPracticesSuppressRequest | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[BestPracticesComplianceModel | Error]:
    """Suppress Security & Compliance Analyzer Best Practice Status

     The HTTP POST request to the `/api/v1/securityAnalyzer/bestPractices/{id}/suppress` path allows you
    to suppress a Security & Compliance Analyzer best practice compliance status that has the specified
    `id`. <p>**Available to**&#58; Veeam Backup Administrator, Veeam Security Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (BestPracticesSuppressRequest | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BestPracticesComplianceModel | Error]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
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
    body: BestPracticesSuppressRequest | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> BestPracticesComplianceModel | Error | None:
    """Suppress Security & Compliance Analyzer Best Practice Status

     The HTTP POST request to the `/api/v1/securityAnalyzer/bestPractices/{id}/suppress` path allows you
    to suppress a Security & Compliance Analyzer best practice compliance status that has the specified
    `id`. <p>**Available to**&#58; Veeam Backup Administrator, Veeam Security Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (BestPracticesSuppressRequest | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BestPracticesComplianceModel | Error
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: BestPracticesSuppressRequest | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[BestPracticesComplianceModel | Error]:
    """Suppress Security & Compliance Analyzer Best Practice Status

     The HTTP POST request to the `/api/v1/securityAnalyzer/bestPractices/{id}/suppress` path allows you
    to suppress a Security & Compliance Analyzer best practice compliance status that has the specified
    `id`. <p>**Available to**&#58; Veeam Backup Administrator, Veeam Security Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (BestPracticesSuppressRequest | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BestPracticesComplianceModel | Error]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: BestPracticesSuppressRequest | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> BestPracticesComplianceModel | Error | None:
    """Suppress Security & Compliance Analyzer Best Practice Status

     The HTTP POST request to the `/api/v1/securityAnalyzer/bestPractices/{id}/suppress` path allows you
    to suppress a Security & Compliance Analyzer best practice compliance status that has the specified
    `id`. <p>**Available to**&#58; Veeam Backup Administrator, Veeam Security Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (BestPracticesSuppressRequest | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BestPracticesComplianceModel | Error
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed

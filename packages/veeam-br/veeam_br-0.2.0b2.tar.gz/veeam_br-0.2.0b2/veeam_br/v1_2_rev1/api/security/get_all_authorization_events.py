import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.authorization_events_result import AuthorizationEventsResult
from ...models.e_authorization_event_state import EAuthorizationEventState
from ...models.e_authorization_events_filters_order_column import EAuthorizationEventsFiltersOrderColumn
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EAuthorizationEventsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    processed_after_filter: datetime.datetime | Unset = UNSET,
    processed_before_filter: datetime.datetime | Unset = UNSET,
    state_filter: EAuthorizationEventState | Unset = UNSET,
    created_by_filter: str | Unset = UNSET,
    processed_by_filter: str | Unset = UNSET,
    expire_before_filter: datetime.datetime | Unset = UNSET,
    expire_after_filter: datetime.datetime | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    params["skip"] = skip

    params["limit"] = limit

    json_order_column: str | Unset = UNSET
    if not isinstance(order_column, Unset):
        json_order_column = order_column.value

    params["orderColumn"] = json_order_column

    params["orderAsc"] = order_asc

    params["nameFilter"] = name_filter

    json_created_after_filter: str | Unset = UNSET
    if not isinstance(created_after_filter, Unset):
        json_created_after_filter = created_after_filter.isoformat()
    params["createdAfterFilter"] = json_created_after_filter

    json_created_before_filter: str | Unset = UNSET
    if not isinstance(created_before_filter, Unset):
        json_created_before_filter = created_before_filter.isoformat()
    params["createdBeforeFilter"] = json_created_before_filter

    json_processed_after_filter: str | Unset = UNSET
    if not isinstance(processed_after_filter, Unset):
        json_processed_after_filter = processed_after_filter.isoformat()
    params["processedAfterFilter"] = json_processed_after_filter

    json_processed_before_filter: str | Unset = UNSET
    if not isinstance(processed_before_filter, Unset):
        json_processed_before_filter = processed_before_filter.isoformat()
    params["processedBeforeFilter"] = json_processed_before_filter

    json_state_filter: str | Unset = UNSET
    if not isinstance(state_filter, Unset):
        json_state_filter = state_filter.value

    params["stateFilter"] = json_state_filter

    params["createdByFilter"] = created_by_filter

    params["processedByFilter"] = processed_by_filter

    json_expire_before_filter: str | Unset = UNSET
    if not isinstance(expire_before_filter, Unset):
        json_expire_before_filter = expire_before_filter.isoformat()
    params["expireBeforeFilter"] = json_expire_before_filter

    json_expire_after_filter: str | Unset = UNSET
    if not isinstance(expire_after_filter, Unset):
        json_expire_after_filter = expire_after_filter.isoformat()
    params["expireAfterFilter"] = json_expire_after_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/authorization/events",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AuthorizationEventsResult | Error | None:
    if response.status_code == 200:
        response_200 = AuthorizationEventsResult.from_dict(response.json())

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
) -> Response[AuthorizationEventsResult | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EAuthorizationEventsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    processed_after_filter: datetime.datetime | Unset = UNSET,
    processed_before_filter: datetime.datetime | Unset = UNSET,
    state_filter: EAuthorizationEventState | Unset = UNSET,
    created_by_filter: str | Unset = UNSET,
    processed_by_filter: str | Unset = UNSET,
    expire_before_filter: datetime.datetime | Unset = UNSET,
    expire_after_filter: datetime.datetime | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[AuthorizationEventsResult | Error]:
    """Get All Authorization Events

     The HTTP GET request to the `/api/v1/authorization/events` path allows you to get an array of
    security-related events. These events cover the following operation types&#58;<ul> <li>Approved and
    rejected requests</li> <li>Updated four-eyes authorization settings</li> <li>Updated settings for
    users and user groups</li> <li>Assigned roles</li> <li>Added or deleted users and user
    groups</li></ul> <p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EAuthorizationEventsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        processed_after_filter (datetime.datetime | Unset):
        processed_before_filter (datetime.datetime | Unset):
        state_filter (EAuthorizationEventState | Unset): Event state.
        created_by_filter (str | Unset):
        processed_by_filter (str | Unset):
        expire_before_filter (datetime.datetime | Unset):
        expire_after_filter (datetime.datetime | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthorizationEventsResult | Error]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        processed_after_filter=processed_after_filter,
        processed_before_filter=processed_before_filter,
        state_filter=state_filter,
        created_by_filter=created_by_filter,
        processed_by_filter=processed_by_filter,
        expire_before_filter=expire_before_filter,
        expire_after_filter=expire_after_filter,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EAuthorizationEventsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    processed_after_filter: datetime.datetime | Unset = UNSET,
    processed_before_filter: datetime.datetime | Unset = UNSET,
    state_filter: EAuthorizationEventState | Unset = UNSET,
    created_by_filter: str | Unset = UNSET,
    processed_by_filter: str | Unset = UNSET,
    expire_before_filter: datetime.datetime | Unset = UNSET,
    expire_after_filter: datetime.datetime | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> AuthorizationEventsResult | Error | None:
    """Get All Authorization Events

     The HTTP GET request to the `/api/v1/authorization/events` path allows you to get an array of
    security-related events. These events cover the following operation types&#58;<ul> <li>Approved and
    rejected requests</li> <li>Updated four-eyes authorization settings</li> <li>Updated settings for
    users and user groups</li> <li>Assigned roles</li> <li>Added or deleted users and user
    groups</li></ul> <p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EAuthorizationEventsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        processed_after_filter (datetime.datetime | Unset):
        processed_before_filter (datetime.datetime | Unset):
        state_filter (EAuthorizationEventState | Unset): Event state.
        created_by_filter (str | Unset):
        processed_by_filter (str | Unset):
        expire_before_filter (datetime.datetime | Unset):
        expire_after_filter (datetime.datetime | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthorizationEventsResult | Error
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        processed_after_filter=processed_after_filter,
        processed_before_filter=processed_before_filter,
        state_filter=state_filter,
        created_by_filter=created_by_filter,
        processed_by_filter=processed_by_filter,
        expire_before_filter=expire_before_filter,
        expire_after_filter=expire_after_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EAuthorizationEventsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    processed_after_filter: datetime.datetime | Unset = UNSET,
    processed_before_filter: datetime.datetime | Unset = UNSET,
    state_filter: EAuthorizationEventState | Unset = UNSET,
    created_by_filter: str | Unset = UNSET,
    processed_by_filter: str | Unset = UNSET,
    expire_before_filter: datetime.datetime | Unset = UNSET,
    expire_after_filter: datetime.datetime | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[AuthorizationEventsResult | Error]:
    """Get All Authorization Events

     The HTTP GET request to the `/api/v1/authorization/events` path allows you to get an array of
    security-related events. These events cover the following operation types&#58;<ul> <li>Approved and
    rejected requests</li> <li>Updated four-eyes authorization settings</li> <li>Updated settings for
    users and user groups</li> <li>Assigned roles</li> <li>Added or deleted users and user
    groups</li></ul> <p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EAuthorizationEventsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        processed_after_filter (datetime.datetime | Unset):
        processed_before_filter (datetime.datetime | Unset):
        state_filter (EAuthorizationEventState | Unset): Event state.
        created_by_filter (str | Unset):
        processed_by_filter (str | Unset):
        expire_before_filter (datetime.datetime | Unset):
        expire_after_filter (datetime.datetime | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthorizationEventsResult | Error]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        processed_after_filter=processed_after_filter,
        processed_before_filter=processed_before_filter,
        state_filter=state_filter,
        created_by_filter=created_by_filter,
        processed_by_filter=processed_by_filter,
        expire_before_filter=expire_before_filter,
        expire_after_filter=expire_after_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    order_column: EAuthorizationEventsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    name_filter: str | Unset = UNSET,
    created_after_filter: datetime.datetime | Unset = UNSET,
    created_before_filter: datetime.datetime | Unset = UNSET,
    processed_after_filter: datetime.datetime | Unset = UNSET,
    processed_before_filter: datetime.datetime | Unset = UNSET,
    state_filter: EAuthorizationEventState | Unset = UNSET,
    created_by_filter: str | Unset = UNSET,
    processed_by_filter: str | Unset = UNSET,
    expire_before_filter: datetime.datetime | Unset = UNSET,
    expire_after_filter: datetime.datetime | Unset = UNSET,
    x_api_version: str = "1.2-rev1",
) -> AuthorizationEventsResult | Error | None:
    """Get All Authorization Events

     The HTTP GET request to the `/api/v1/authorization/events` path allows you to get an array of
    security-related events. These events cover the following operation types&#58;<ul> <li>Approved and
    rejected requests</li> <li>Updated four-eyes authorization settings</li> <li>Updated settings for
    users and user groups</li> <li>Assigned roles</li> <li>Added or deleted users and user
    groups</li></ul> <p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):
        order_column (EAuthorizationEventsFiltersOrderColumn | Unset):
        order_asc (bool | Unset):
        name_filter (str | Unset):
        created_after_filter (datetime.datetime | Unset):
        created_before_filter (datetime.datetime | Unset):
        processed_after_filter (datetime.datetime | Unset):
        processed_before_filter (datetime.datetime | Unset):
        state_filter (EAuthorizationEventState | Unset): Event state.
        created_by_filter (str | Unset):
        processed_by_filter (str | Unset):
        expire_before_filter (datetime.datetime | Unset):
        expire_after_filter (datetime.datetime | Unset):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthorizationEventsResult | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            created_after_filter=created_after_filter,
            created_before_filter=created_before_filter,
            processed_after_filter=processed_after_filter,
            processed_before_filter=processed_before_filter,
            state_filter=state_filter,
            created_by_filter=created_by_filter,
            processed_by_filter=processed_by_filter,
            expire_before_filter=expire_before_filter,
            expire_after_filter=expire_after_filter,
            x_api_version=x_api_version,
        )
    ).parsed

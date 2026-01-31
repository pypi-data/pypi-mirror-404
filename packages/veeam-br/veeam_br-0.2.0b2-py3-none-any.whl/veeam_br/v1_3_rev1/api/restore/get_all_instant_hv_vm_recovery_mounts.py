from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_instant_hv_vm_recovery_mounts_filters_order_column import EInstantHvVMRecoveryMountsFiltersOrderColumn
from ...models.e_instant_recovery_mount_state import EInstantRecoveryMountState
from ...models.error import Error
from ...models.instant_hv_vm_recovery_mounts_result import InstantHvVMRecoveryMountsResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EInstantHvVMRecoveryMountsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    state_filter: EInstantRecoveryMountState | Unset = UNSET,
    vm_name_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
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

    json_state_filter: str | Unset = UNSET
    if not isinstance(state_filter, Unset):
        json_state_filter = state_filter.value

    params["stateFilter"] = json_state_filter

    params["vmNameFilter"] = vm_name_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/restore/instantRecovery/hyperV/vm",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | InstantHvVMRecoveryMountsResult | None:
    if response.status_code == 200:
        response_200 = InstantHvVMRecoveryMountsResult.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = Error.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = Error.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = Error.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Error | InstantHvVMRecoveryMountsResult]:
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
    limit: int | Unset = 200,
    order_column: EInstantHvVMRecoveryMountsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    state_filter: EInstantRecoveryMountState | Unset = UNSET,
    vm_name_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | InstantHvVMRecoveryMountsResult]:
    """Get All Instant Recovery Mount Points of Microsoft Hyper-V VMs

     The HTTP GET request to the `/api/v1/restore/instantRecovery/hyperV/vm` endpoint gets an array of
    Instant Recovery mount points of Microsoft Hyper-V VMs.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer, Veeam Security Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EInstantHvVMRecoveryMountsFiltersOrderColumn | Unset): Sorts mount points by
            one of the mount point parameters.
        order_asc (bool | Unset):
        state_filter (EInstantRecoveryMountState | Unset): Mount state.
        vm_name_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | InstantHvVMRecoveryMountsResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        state_filter=state_filter,
        vm_name_filter=vm_name_filter,
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
    limit: int | Unset = 200,
    order_column: EInstantHvVMRecoveryMountsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    state_filter: EInstantRecoveryMountState | Unset = UNSET,
    vm_name_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Error | InstantHvVMRecoveryMountsResult | None:
    """Get All Instant Recovery Mount Points of Microsoft Hyper-V VMs

     The HTTP GET request to the `/api/v1/restore/instantRecovery/hyperV/vm` endpoint gets an array of
    Instant Recovery mount points of Microsoft Hyper-V VMs.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer, Veeam Security Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EInstantHvVMRecoveryMountsFiltersOrderColumn | Unset): Sorts mount points by
            one of the mount point parameters.
        order_asc (bool | Unset):
        state_filter (EInstantRecoveryMountState | Unset): Mount state.
        vm_name_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | InstantHvVMRecoveryMountsResult
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        state_filter=state_filter,
        vm_name_filter=vm_name_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EInstantHvVMRecoveryMountsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    state_filter: EInstantRecoveryMountState | Unset = UNSET,
    vm_name_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Error | InstantHvVMRecoveryMountsResult]:
    """Get All Instant Recovery Mount Points of Microsoft Hyper-V VMs

     The HTTP GET request to the `/api/v1/restore/instantRecovery/hyperV/vm` endpoint gets an array of
    Instant Recovery mount points of Microsoft Hyper-V VMs.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer, Veeam Security Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EInstantHvVMRecoveryMountsFiltersOrderColumn | Unset): Sorts mount points by
            one of the mount point parameters.
        order_asc (bool | Unset):
        state_filter (EInstantRecoveryMountState | Unset): Mount state.
        vm_name_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | InstantHvVMRecoveryMountsResult]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        state_filter=state_filter,
        vm_name_filter=vm_name_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    skip: int | Unset = UNSET,
    limit: int | Unset = 200,
    order_column: EInstantHvVMRecoveryMountsFiltersOrderColumn | Unset = UNSET,
    order_asc: bool | Unset = UNSET,
    state_filter: EInstantRecoveryMountState | Unset = UNSET,
    vm_name_filter: str | Unset = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Error | InstantHvVMRecoveryMountsResult | None:
    """Get All Instant Recovery Mount Points of Microsoft Hyper-V VMs

     The HTTP GET request to the `/api/v1/restore/instantRecovery/hyperV/vm` endpoint gets an array of
    Instant Recovery mount points of Microsoft Hyper-V VMs.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer, Veeam Security Administrator.</p>

    Args:
        skip (int | Unset):
        limit (int | Unset):  Default: 200.
        order_column (EInstantHvVMRecoveryMountsFiltersOrderColumn | Unset): Sorts mount points by
            one of the mount point parameters.
        order_asc (bool | Unset):
        state_filter (EInstantRecoveryMountState | Unset): Mount state.
        vm_name_filter (str | Unset):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | InstantHvVMRecoveryMountsResult
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            state_filter=state_filter,
            vm_name_filter=vm_name_filter,
            x_api_version=x_api_version,
        )
    ).parsed

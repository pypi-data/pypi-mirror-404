from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.job_submit_response import JobSubmitResponse
from ...models.simulation_request import SimulationRequest
from ...types import Response


def _get_kwargs(
    *,
    body: SimulationRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/simulate/economy/comparison",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | JobSubmitResponse | None:
    if response.status_code == 200:
        response_200 = JobSubmitResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | HTTPValidationError | JobSubmitResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SimulationRequest,
) -> Response[Any | HTTPValidationError | JobSubmitResponse]:
    """Submit Simulation

     Submit a simulation job.

    Routes to the appropriate simulation app based on country and version.
    Returns immediately with a job_id for polling.

    Args:
        body (SimulationRequest): Request model for simulation submission.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | JobSubmitResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: SimulationRequest,
) -> Any | HTTPValidationError | JobSubmitResponse | None:
    """Submit Simulation

     Submit a simulation job.

    Routes to the appropriate simulation app based on country and version.
    Returns immediately with a job_id for polling.

    Args:
        body (SimulationRequest): Request model for simulation submission.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | JobSubmitResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SimulationRequest,
) -> Response[Any | HTTPValidationError | JobSubmitResponse]:
    """Submit Simulation

     Submit a simulation job.

    Routes to the appropriate simulation app based on country and version.
    Returns immediately with a job_id for polling.

    Args:
        body (SimulationRequest): Request model for simulation submission.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError | JobSubmitResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: SimulationRequest,
) -> Any | HTTPValidationError | JobSubmitResponse | None:
    """Submit Simulation

     Submit a simulation job.

    Routes to the appropriate simulation app based on country and version.
    Returns immediately with a job_id for polling.

    Args:
        body (SimulationRequest): Request model for simulation submission.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError | JobSubmitResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed

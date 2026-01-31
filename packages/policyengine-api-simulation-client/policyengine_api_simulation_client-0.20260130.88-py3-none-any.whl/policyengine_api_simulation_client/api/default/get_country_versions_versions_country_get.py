from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_country_versions_versions_country_get_response_get_country_versions_versions_country_get import (
    GetCountryVersionsVersionsCountryGetResponseGetCountryVersionsVersionsCountryGet,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    country: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/versions/{country}".format(
            country=quote(str(country), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetCountryVersionsVersionsCountryGetResponseGetCountryVersionsVersionsCountryGet | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = GetCountryVersionsVersionsCountryGetResponseGetCountryVersionsVersionsCountryGet.from_dict(
            response.json()
        )

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[GetCountryVersionsVersionsCountryGetResponseGetCountryVersionsVersionsCountryGet | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    country: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetCountryVersionsVersionsCountryGetResponseGetCountryVersionsVersionsCountryGet | HTTPValidationError]:
    """Get Country Versions

     Get available versions for a specific country.

    Args:
        country (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetCountryVersionsVersionsCountryGetResponseGetCountryVersionsVersionsCountryGet | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        country=country,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    country: str,
    *,
    client: AuthenticatedClient | Client,
) -> GetCountryVersionsVersionsCountryGetResponseGetCountryVersionsVersionsCountryGet | HTTPValidationError | None:
    """Get Country Versions

     Get available versions for a specific country.

    Args:
        country (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetCountryVersionsVersionsCountryGetResponseGetCountryVersionsVersionsCountryGet | HTTPValidationError
    """

    return sync_detailed(
        country=country,
        client=client,
    ).parsed


async def asyncio_detailed(
    country: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetCountryVersionsVersionsCountryGetResponseGetCountryVersionsVersionsCountryGet | HTTPValidationError]:
    """Get Country Versions

     Get available versions for a specific country.

    Args:
        country (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetCountryVersionsVersionsCountryGetResponseGetCountryVersionsVersionsCountryGet | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        country=country,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    country: str,
    *,
    client: AuthenticatedClient | Client,
) -> GetCountryVersionsVersionsCountryGetResponseGetCountryVersionsVersionsCountryGet | HTTPValidationError | None:
    """Get Country Versions

     Get available versions for a specific country.

    Args:
        country (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetCountryVersionsVersionsCountryGetResponseGetCountryVersionsVersionsCountryGet | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            country=country,
            client=client,
        )
    ).parsed

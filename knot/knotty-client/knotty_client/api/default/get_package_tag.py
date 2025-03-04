from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import Client
from ...models.http_validation_error import HTTPValidationError
from ...models.not_found_error_model import NotFoundErrorModel
from ...models.package_tag import PackageTag
from ...types import Response


def _get_kwargs(
    package: str,
    tag: str,
    *,
    client: Client,
) -> Dict[str, Any]:
    url = "{}/package/{package}/tag/{tag}".format(client.base_url, package=package, tag=tag)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "follow_redirects": client.follow_redirects,
    }


def _parse_response(
    *, client: Client, response: httpx.Response
) -> Optional[Union[HTTPValidationError, NotFoundErrorModel, PackageTag]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = PackageTag.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.NOT_FOUND:
        response_404 = NotFoundErrorModel.from_dict(response.json())

        return response_404
    if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Client, response: httpx.Response
) -> Response[Union[HTTPValidationError, NotFoundErrorModel, PackageTag]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    package: str,
    tag: str,
    *,
    client: Client,
) -> Response[Union[HTTPValidationError, NotFoundErrorModel, PackageTag]]:
    """Get Package Tag

    Args:
        package (str):
        tag (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, NotFoundErrorModel, PackageTag]]
    """

    kwargs = _get_kwargs(
        package=package,
        tag=tag,
        client=client,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    package: str,
    tag: str,
    *,
    client: Client,
) -> Optional[Union[HTTPValidationError, NotFoundErrorModel, PackageTag]]:
    """Get Package Tag

    Args:
        package (str):
        tag (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, NotFoundErrorModel, PackageTag]
    """

    return sync_detailed(
        package=package,
        tag=tag,
        client=client,
    ).parsed


async def asyncio_detailed(
    package: str,
    tag: str,
    *,
    client: Client,
) -> Response[Union[HTTPValidationError, NotFoundErrorModel, PackageTag]]:
    """Get Package Tag

    Args:
        package (str):
        tag (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, NotFoundErrorModel, PackageTag]]
    """

    kwargs = _get_kwargs(
        package=package,
        tag=tag,
        client=client,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    package: str,
    tag: str,
    *,
    client: Client,
) -> Optional[Union[HTTPValidationError, NotFoundErrorModel, PackageTag]]:
    """Get Package Tag

    Args:
        package (str):
        tag (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, NotFoundErrorModel, PackageTag]
    """

    return (
        await asyncio_detailed(
            package=package,
            tag=tag,
            client=client,
        )
    ).parsed

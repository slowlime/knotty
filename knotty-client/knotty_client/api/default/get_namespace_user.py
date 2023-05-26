from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import Client
from ...models.http_validation_error import HTTPValidationError
from ...models.namespace_user import NamespaceUser
from ...models.not_found_error_model import NotFoundErrorModel
from ...types import Response


def _get_kwargs(
    namespace: str,
    username: str,
    *,
    client: Client,
) -> Dict[str, Any]:
    url = "{}/namespace/{namespace}/user/{username}".format(client.base_url, namespace=namespace, username=username)

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
) -> Optional[Union[HTTPValidationError, NamespaceUser, NotFoundErrorModel]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = NamespaceUser.from_dict(response.json())

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
) -> Response[Union[HTTPValidationError, NamespaceUser, NotFoundErrorModel]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    namespace: str,
    username: str,
    *,
    client: Client,
) -> Response[Union[HTTPValidationError, NamespaceUser, NotFoundErrorModel]]:
    """Get Namespace User

    Args:
        namespace (str):
        username (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, NamespaceUser, NotFoundErrorModel]]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        username=username,
        client=client,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    namespace: str,
    username: str,
    *,
    client: Client,
) -> Optional[Union[HTTPValidationError, NamespaceUser, NotFoundErrorModel]]:
    """Get Namespace User

    Args:
        namespace (str):
        username (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, NamespaceUser, NotFoundErrorModel]
    """

    return sync_detailed(
        namespace=namespace,
        username=username,
        client=client,
    ).parsed


async def asyncio_detailed(
    namespace: str,
    username: str,
    *,
    client: Client,
) -> Response[Union[HTTPValidationError, NamespaceUser, NotFoundErrorModel]]:
    """Get Namespace User

    Args:
        namespace (str):
        username (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, NamespaceUser, NotFoundErrorModel]]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        username=username,
        client=client,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    namespace: str,
    username: str,
    *,
    client: Client,
) -> Optional[Union[HTTPValidationError, NamespaceUser, NotFoundErrorModel]]:
    """Get Namespace User

    Args:
        namespace (str):
        username (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, NamespaceUser, NotFoundErrorModel]
    """

    return (
        await asyncio_detailed(
            namespace=namespace,
            username=username,
            client=client,
        )
    ).parsed

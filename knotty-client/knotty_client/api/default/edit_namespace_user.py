from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.http_validation_error import HTTPValidationError
from ...models.message import Message
from ...models.namespace_user_edit import NamespaceUserEdit
from ...models.not_found_error_model import NotFoundErrorModel
from ...types import Response


def _get_kwargs(
    namespace: str,
    username: str,
    *,
    client: AuthenticatedClient,
    json_body: NamespaceUserEdit,
) -> Dict[str, Any]:
    url = "{}/namespace/{namespace}/user/{username}".format(client.base_url, namespace=namespace, username=username)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    json_json_body = json_body.to_dict()

    return {
        "method": "post",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "follow_redirects": client.follow_redirects,
        "json": json_json_body,
    }


def _parse_response(
    *, client: Client, response: httpx.Response
) -> Optional[Union[ErrorModel, HTTPValidationError, Message, NotFoundErrorModel]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = Message.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.NOT_FOUND:
        response_404 = NotFoundErrorModel.from_dict(response.json())

        return response_404
    if response.status_code == HTTPStatus.FORBIDDEN:
        response_403 = ErrorModel.from_dict(response.json())

        return response_403
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = ErrorModel.from_dict(response.json())

        return response_400
    if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Client, response: httpx.Response
) -> Response[Union[ErrorModel, HTTPValidationError, Message, NotFoundErrorModel]]:
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
    client: AuthenticatedClient,
    json_body: NamespaceUserEdit,
) -> Response[Union[ErrorModel, HTTPValidationError, Message, NotFoundErrorModel]]:
    """Edit Namespace User

    Args:
        namespace (str):
        username (str):
        json_body (NamespaceUserEdit):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorModel, HTTPValidationError, Message, NotFoundErrorModel]]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        username=username,
        client=client,
        json_body=json_body,
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
    client: AuthenticatedClient,
    json_body: NamespaceUserEdit,
) -> Optional[Union[ErrorModel, HTTPValidationError, Message, NotFoundErrorModel]]:
    """Edit Namespace User

    Args:
        namespace (str):
        username (str):
        json_body (NamespaceUserEdit):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorModel, HTTPValidationError, Message, NotFoundErrorModel]
    """

    return sync_detailed(
        namespace=namespace,
        username=username,
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    namespace: str,
    username: str,
    *,
    client: AuthenticatedClient,
    json_body: NamespaceUserEdit,
) -> Response[Union[ErrorModel, HTTPValidationError, Message, NotFoundErrorModel]]:
    """Edit Namespace User

    Args:
        namespace (str):
        username (str):
        json_body (NamespaceUserEdit):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorModel, HTTPValidationError, Message, NotFoundErrorModel]]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        username=username,
        client=client,
        json_body=json_body,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    namespace: str,
    username: str,
    *,
    client: AuthenticatedClient,
    json_body: NamespaceUserEdit,
) -> Optional[Union[ErrorModel, HTTPValidationError, Message, NotFoundErrorModel]]:
    """Edit Namespace User

    Args:
        namespace (str):
        username (str):
        json_body (NamespaceUserEdit):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorModel, HTTPValidationError, Message, NotFoundErrorModel]
    """

    return (
        await asyncio_detailed(
            namespace=namespace,
            username=username,
            client=client,
            json_body=json_body,
        )
    ).parsed

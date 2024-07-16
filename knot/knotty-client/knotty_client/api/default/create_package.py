from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.already_exists_error_model import AlreadyExistsErrorModel
from ...models.error_model import ErrorModel
from ...models.http_validation_error import HTTPValidationError
from ...models.message import Message
from ...models.not_found_error_model import NotFoundErrorModel
from ...models.package_create import PackageCreate
from ...models.unknown_dependencies_error_model import UnknownDependenciesErrorModel
from ...types import Response


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    json_body: PackageCreate,
) -> Dict[str, Any]:
    url = "{}/package".format(client.base_url)

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
) -> Optional[
    Union[
        AlreadyExistsErrorModel,
        ErrorModel,
        HTTPValidationError,
        Message,
        NotFoundErrorModel,
        UnknownDependenciesErrorModel,
    ]
]:
    if response.status_code == HTTPStatus.CREATED:
        response_201 = Message.from_dict(response.json())

        return response_201
    if response.status_code == HTTPStatus.UNAUTHORIZED:
        response_401 = ErrorModel.from_dict(response.json())

        return response_401
    if response.status_code == HTTPStatus.FORBIDDEN:
        response_403 = ErrorModel.from_dict(response.json())

        return response_403
    if response.status_code == HTTPStatus.NOT_FOUND:
        response_404 = NotFoundErrorModel.from_dict(response.json())

        return response_404
    if response.status_code == HTTPStatus.CONFLICT:
        response_409 = AlreadyExistsErrorModel.from_dict(response.json())

        return response_409
    if response.status_code == HTTPStatus.BAD_REQUEST:
        response_400 = UnknownDependenciesErrorModel.from_dict(response.json())

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
) -> Response[
    Union[
        AlreadyExistsErrorModel,
        ErrorModel,
        HTTPValidationError,
        Message,
        NotFoundErrorModel,
        UnknownDependenciesErrorModel,
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    json_body: PackageCreate,
) -> Response[
    Union[
        AlreadyExistsErrorModel,
        ErrorModel,
        HTTPValidationError,
        Message,
        NotFoundErrorModel,
        UnknownDependenciesErrorModel,
    ]
]:
    """Create Package

    Args:
        json_body (PackageCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AlreadyExistsErrorModel, ErrorModel, HTTPValidationError, Message, NotFoundErrorModel, UnknownDependenciesErrorModel]]
    """

    kwargs = _get_kwargs(
        client=client,
        json_body=json_body,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    json_body: PackageCreate,
) -> Optional[
    Union[
        AlreadyExistsErrorModel,
        ErrorModel,
        HTTPValidationError,
        Message,
        NotFoundErrorModel,
        UnknownDependenciesErrorModel,
    ]
]:
    """Create Package

    Args:
        json_body (PackageCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AlreadyExistsErrorModel, ErrorModel, HTTPValidationError, Message, NotFoundErrorModel, UnknownDependenciesErrorModel]
    """

    return sync_detailed(
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    json_body: PackageCreate,
) -> Response[
    Union[
        AlreadyExistsErrorModel,
        ErrorModel,
        HTTPValidationError,
        Message,
        NotFoundErrorModel,
        UnknownDependenciesErrorModel,
    ]
]:
    """Create Package

    Args:
        json_body (PackageCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AlreadyExistsErrorModel, ErrorModel, HTTPValidationError, Message, NotFoundErrorModel, UnknownDependenciesErrorModel]]
    """

    kwargs = _get_kwargs(
        client=client,
        json_body=json_body,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    json_body: PackageCreate,
) -> Optional[
    Union[
        AlreadyExistsErrorModel,
        ErrorModel,
        HTTPValidationError,
        Message,
        NotFoundErrorModel,
        UnknownDependenciesErrorModel,
    ]
]:
    """Create Package

    Args:
        json_body (PackageCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AlreadyExistsErrorModel, ErrorModel, HTTPValidationError, Message, NotFoundErrorModel, UnknownDependenciesErrorModel]
    """

    return (
        await asyncio_detailed(
            client=client,
            json_body=json_body,
        )
    ).parsed

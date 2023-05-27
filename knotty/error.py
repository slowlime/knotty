from typing import Any, ClassVar
from fastapi import status

from knotty.schema import ErrorModel


class KnottyException(Exception):
    Model: ClassVar[type[ErrorModel]]

    status_code: ClassVar[int]
    description: ClassVar[str]

    detail: str
    headers: dict[str, str] | None

    def __init__(
        self, detail: str | None = None, headers: dict[str, str] | None = None
    ):
        if detail is None:
            detail = self.description

        self.detail = detail
        self.headers = headers

    def __init_subclass__(
        cls,
        /,
        status_code: int,
        description: str,
        model: type[ErrorModel] | None = None,
        **kwargs,
    ):
        super().__init_subclass__(**kwargs)
        cls.Model = model or ErrorModel

        cls.status_code = status_code
        cls.description = description

    @property
    def data(self) -> ErrorModel:
        return ErrorModel(detail=self.detail)


class UnauthorizedException(
    KnottyException,
    status_code=status.HTTP_401_UNAUTHORIZED,
    description="Could not authenticate the user",
):
    def __init__(self, detail: str | None):
        super().__init__(detail=detail, headers={"WWW-Authenticate": "Bearer"})


class InvalidCredentialsException(
    KnottyException,
    status_code=status.HTTP_401_UNAUTHORIZED,
    description="Invalid username and/or password",
):
    def __init__(self):
        super().__init__(headers={"WWW-Authenticate": "Bearer"})


class NoPermissionException(
    KnottyException,
    status_code=status.HTTP_403_FORBIDDEN,
    description="Access denied due to insufficient permissions",
):
    pass


class UsernameTakenException(
    KnottyException,
    status_code=status.HTTP_400_BAD_REQUEST,
    description="Username is already taken",
):
    pass


class EmailRegisteredException(
    KnottyException,
    status_code=status.HTTP_400_BAD_REQUEST,
    description="Email is already registered",
):
    pass


class NotFoundErrorModel(ErrorModel):
    what: str | None


class NotFoundException(
    KnottyException,
    status_code=status.HTTP_404_NOT_FOUND,
    description="Resource not found",
    model=NotFoundErrorModel,
):
    what: str

    def __init__(self, what: str):
        super().__init__(
            detail=f"{what} not found",
        )

        self.what = what

    @property
    def data(self) -> NotFoundErrorModel:
        return NotFoundErrorModel(what=self.what, **super().data.dict())


class AlreadyExistsErrorModel(ErrorModel):
    what: str


class AlreadyExistsException(
    KnottyException,
    status_code=status.HTTP_409_CONFLICT,
    description="Resource already exists",
    model=AlreadyExistsErrorModel,
):
    what: str

    def __init__(self, what: str):
        super().__init__(
            detail=f"{what} already exists",
        )

        self.what = what

    @property
    def data(self) -> AlreadyExistsErrorModel:
        return AlreadyExistsErrorModel(
            what=self.what,
            **super().data.dict(),
        )


class NoNamespaceOwnerRemainsException(
    KnottyException,
    status_code=status.HTTP_400_BAD_REQUEST,
    description="Operation would leave namespace without owner",
):
    pass


class NoPackageOwnerRemainsException(
    KnottyException,
    status_code=status.HTTP_400_BAD_REQUEST,
    description="Operation would leave package without owner",
):
    pass


class RoleNotEmptyException(
    KnottyException,
    status_code=status.HTTP_400_BAD_REQUEST,
    description="Cannot remove namespace role with members",
):
    pass


class UnknownOwnersErrorModel(ErrorModel):
    usernames: list[str]


class UnknownOwnersException(
    KnottyException,
    status_code=status.HTTP_400_BAD_REQUEST,
    description="Owner list includes unknown users",
    model=UnknownOwnersErrorModel,
):
    usernames: list[str]

    def __init__(self, usernames: list[str]):
        detail = "Owner list includes unknown user"

        if len(usernames) != 1:
            detail += "s"

        if usernames:
            detail += " " + ", ".join(usernames)

        super().__init__(
            detail=detail,
        )

        self.usernames = usernames

    @property
    def data(self) -> UnknownOwnersErrorModel:
        return UnknownOwnersErrorModel(
            usernames=self.usernames,
            **super().data.dict(),
        )


class UnknownDependenciesErrorModel(ErrorModel):
    packages: list[str]


class UnknownDependenciesException(
    KnottyException,
    status_code=status.HTTP_400_BAD_REQUEST,
    description="Package requires unknown dependencies",
    model=UnknownDependenciesErrorModel,
):
    packages: list[str]

    def __init__(self, packages: list[str]):
        match packages:
            case []:
                detail = "Package requires unknown dependencies"

            case [package]:
                detail = f"Package requires unknown dependency {package}"

            case _:
                detail = "Package requires unknown dependencies {}".format(
                    ", ".join(packages)
                )

        super().__init__(
            detail=detail,
        )

        self.packages = packages

    @property
    def data(self) -> UnknownDependenciesErrorModel:
        return UnknownDependenciesErrorModel(
            packages=self.packages,
            **super().data.dict(),
        )


class HasDependentsException(
    KnottyException,
    status_code=status.HTTP_400_BAD_REQUEST,
    description="Package has dependent packages",
):
    pass


class HasReferringTagsException(
    KnottyException,
    status_code=status.HTTP_400_BAD_REQUEST,
    description="Package has tags referring to this version",
):
    pass


def exception_responses(
    *exceptions: type[KnottyException],
) -> dict[int | str, dict[str, Any]]:
    return {
        exception.status_code: {
            "description": exception.description,
            "model": exception.Model,
        }
        for exception in exceptions
    }

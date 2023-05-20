from fastapi import HTTPException, status


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not authenticate the user",
        headers={"WWW-Authenticate": "Bearer"},
    )


def invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username and/or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


def no_permission() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied due to insufficient permissions",
    )


def username_taken() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Username is already taken",
    )


def email_registered() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Email is already registered",
    )


def not_found(what: str | None = None) -> HTTPException:
    detail = f"{what} not found" if what is not None else None

    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail,
    )


def already_exists(what: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"{what} already exists",
    )


def no_owner_remains() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Operation would leave namespace without owner",
    )


def role_not_empty() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Cannot remove namespace role with members",
    )

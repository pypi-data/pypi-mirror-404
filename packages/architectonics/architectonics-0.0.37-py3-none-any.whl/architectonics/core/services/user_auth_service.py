from uuid import UUID

from fastapi import Depends, Header, HTTPException
from starlette.status import HTTP_400_BAD_REQUEST


def get_user_id(
    x_user_id: str = Header(
        alias="X-User-Id",
        description="Идентификатор пользователя",
    ),
) -> str:
    if not x_user_id:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="X-User-Id header is required",
        )

    try:
        _ = UUID(x_user_id, version=4)  # version=4 для проверки UUID v4
    except ValueError:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="not_valid_uuid",
        )

    return x_user_id


def get_user_roles(
    x_user_roles: str = Header(
        alias="X-User-Roles",
        description="Роли пользователя",
    ),
) -> str:
    if not x_user_roles:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="X-User-Roles header is required",
        )

    return x_user_roles.split(",")


class UserAuthService:
    def __init__(
        self,
        user_id: str = Depends(get_user_id),
        user_roles: list[str] = Depends(get_user_roles),
    ):
        self.user_id = user_id
        self.user_roles = user_roles

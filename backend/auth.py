"""fastapi-users authentication: JWT bearer tokens."""

import os
import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.models import User

SECRET = os.getenv(
    "SECRET_KEY",
    "CHANGE-THIS-IN-PRODUCTION-USE-A-RANDOM-256-BIT-KEY",
)

# ── Transport + strategy ──────────────────────────────────────────────────────

bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=SECRET,
        lifetime_seconds=60 * 60 * 24 * 7,  # 7 days
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


# ── User manager ──────────────────────────────────────────────────────────────


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(
        self, user: User, request: Optional[Request] = None
    ) -> None:
        print(f"[auth] User {user.id} registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ) -> None:
        # TODO: send reset email via your preferred provider
        print(f"[auth] Password reset token for {user.id}: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ) -> None:
        # TODO: send verification email
        print(f"[auth] Verification token for {user.id}: {token}")


# ── Dependencies ──────────────────────────────────────────────────────────────


async def get_user_db(session: AsyncSession = Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


# ── FastAPIUsers instance (re-used in main.py and route guards) ───────────────

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)

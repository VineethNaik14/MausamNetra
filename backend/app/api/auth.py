from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.logging import get_logger
from app.core.security import create_access_token, verify_password
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.core.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import ApiResponse
from app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)


@router.post("/login", response_model=ApiResponse[TokenResponse], summary="Login and obtain a JWT access token")
def login(payload: LoginRequest, db: Session = Depends(get_db_session)):
    user = UserRepository(db).get_by_email(payload.email.lower())

    # Deliberately use the same error for "no such user" and "wrong password"
    # to avoid leaking which emails are registered.
    if user is None or not verify_password(payload.password, user.password_hash):
        logger.info("Failed login attempt for email=%s", payload.email)
        raise UnauthorizedError("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedError("User account is inactive")

    token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
    logger.info("User %s logged in", user.id)

    return ApiResponse(
        data=TokenResponse(
            access_token=token,
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user=UserRead.model_validate(user),
        ),
        message="Login successful",
    )


@router.get("/me", response_model=ApiResponse[UserRead], summary="Get the currently authenticated user")
def get_me(current_user: User = Depends(get_current_user)):
    return ApiResponse(data=UserRead.model_validate(current_user))


@router.post("/logout", response_model=ApiResponse[None], summary="Logout (client-side token discard)")
def logout(current_user: User = Depends(get_current_user)):
    # Stateless JWTs: logout is handled client-side by discarding the token.
    # A token-blocklist could be added later (e.g. Redis) if immediate
    # server-side revocation becomes a requirement.
    logger.info("User %s logged out", current_user.id)
    return ApiResponse(data=None, message="Logged out")

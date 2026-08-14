from fastapi import APIRouter, Request

from app.api.dependencies import get_current_user
from app.schemas.auth import (
    ActionMessage,
    EmailVerificationConfirm,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import (
    confirm_email_verification,
    confirm_password_reset,
    current_user,
    login,
    logout,
    refresh,
    register,
    request_password_reset,
)
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from app.api.dependencies import bearer

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=UserResponse, status_code=201)
async def register_account(payload: RegisterRequest) -> UserResponse:
    return register(payload)


@router.post("/auth/login", response_model=TokenResponse)
async def login_account(payload: LoginRequest, request: Request) -> TokenResponse:
    return login(payload, user_agent=request.headers.get("user-agent"), ip_address=request.client.host if request.client else None)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_tokens(payload: RefreshTokenRequest, request: Request) -> TokenResponse:
    return refresh(payload.refresh_token, user_agent=request.headers.get("user-agent"), ip_address=request.client.host if request.client else None)


@router.post("/auth/password-reset/request", response_model=ActionMessage)
async def password_reset_request(payload: PasswordResetRequest) -> ActionMessage:
    request_password_reset(payload)
    return ActionMessage(message="If the account exists, password reset instructions will be sent")


@router.post("/auth/password-reset/confirm", response_model=ActionMessage)
async def password_reset_confirmation(payload: PasswordResetConfirm) -> ActionMessage:
    confirm_password_reset(payload)
    return ActionMessage(message="Password reset completed")


@router.post("/auth/verify-email", response_model=ActionMessage)
async def verify_email(payload: EmailVerificationConfirm) -> ActionMessage:
    confirm_email_verification(payload)
    return ActionMessage(message="Email verified successfully")


@router.get("/user/me", response_model=UserResponse)
@router.get("/auth/me", response_model=UserResponse)
async def get_user_me(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> UserResponse:
    user = current_user(credentials)
    request.state.user_id = str(user.id)
    return user


@router.post("/auth/logout", response_model=ActionMessage)
async def logout_account(payload: LogoutRequest, user: UserResponse = Depends(get_current_user)) -> ActionMessage:
    logout(payload.refresh_token, user.id)
    return ActionMessage(message="Logged out successfully")

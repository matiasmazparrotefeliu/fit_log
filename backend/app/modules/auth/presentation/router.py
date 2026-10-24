"""Routers del módulo auth (Fase 2).

Endpoints:
- POST /auth/register   (público)      → UserRead
- POST /auth/login      (público)      → TokenResponse
- GET  /users/me        (autenticado)  → UserRead
- PATCH /users/me       (autenticado)  → UserRead
- GET  /users           (super_admin)  → UserListResponse
- POST /users           (super_admin)  → UserRead
"""

from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.rbac import require_role
from app.modules.auth.application.dto import (
    CreateUserInput,
    LoginInput,
    RegisterUserInput,
    UpdateProfileInput,
)
from app.modules.auth.application.use_cases import (
    CreateUser,
    ListUsers,
    LoginUser,
    RegisterUser,
    UpdateProfile,
)
from app.modules.auth.domain.entities import User, UserRole
from app.modules.auth.domain.errors import (
    EmailAlreadyExists,
    InvalidCredentials,
    InvalidRoleAssignment,
)
from app.modules.auth.domain.ports import UserRepository
from app.modules.auth.presentation.dependencies import (
    get_current_user,
    get_user_repository,
)
from app.modules.auth.presentation.schemas import (
    ErrorResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserCreate,
    UserListResponse,
    UserRead,
    UserUpdate,
)
from app.shared.pagination import PageParams

auth_router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])


@auth_router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="Registro público de un runner",
)
def register(
    payload: RegisterRequest,
    repository: UserRepository = Depends(get_user_repository),
) -> UserRead:
    try:
        user = RegisterUser(repository).execute(
            RegisterUserInput(
                email=str(payload.email),
                password=payload.password,
                full_name=payload.full_name,
                birth_date=payload.birth_date,
                weight_kg=payload.weight_kg,
            )
        )
    except EmailAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    return UserRead.model_validate(user)


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={401: {"model": ErrorResponse}},
    summary="Inicio de sesión (emite JWT)",
)
def login(
    payload: LoginRequest,
    repository: UserRepository = Depends(get_user_repository),
) -> TokenResponse:
    try:
        _, token = LoginUser(repository).execute(
            LoginInput(email=str(payload.email), password=payload.password)
        )
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=token)


@users_router.get(
    "/me",
    response_model=UserRead,
    responses={401: {"model": ErrorResponse}},
    summary="Perfil del usuario autenticado",
)
def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@users_router.patch(
    "/me",
    response_model=UserRead,
    responses={401: {"model": ErrorResponse}},
    summary="Actualiza el perfil del usuario autenticado",
)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    repository: UserRepository = Depends(get_user_repository),
) -> UserRead:
    user = UpdateProfile(repository).execute(
        current_user,
        UpdateProfileInput(
            full_name=payload.full_name,
            birth_date=payload.birth_date,
            weight_kg=payload.weight_kg,
        ),
    )
    return UserRead.model_validate(user)


@users_router.get(
    "",
    response_model=UserListResponse,
    dependencies=[Depends(require_role(UserRole.SUPER_ADMIN.value))],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    summary="Lista usuarios (solo super_admin)",
)
def list_users(
    params: PageParams = Depends(),
    repository: UserRepository = Depends(get_user_repository),
) -> UserListResponse:
    users, total = ListUsers(repository).execute(offset=params.offset, limit=params.limit)
    pages = ceil(total / params.size) if params.size else 0
    return UserListResponse(
        items=[UserRead.model_validate(user) for user in users],
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )


@users_router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.SUPER_ADMIN.value))],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
    summary="Crea un usuario admin/runner (solo super_admin)",
)
def create_user(
    payload: UserCreate,
    repository: UserRepository = Depends(get_user_repository),
) -> UserRead:
    try:
        user = CreateUser(repository).execute(
            CreateUserInput(
                email=str(payload.email),
                password=payload.password,
                full_name=payload.full_name,
                role=UserRole(payload.role),
                birth_date=payload.birth_date,
                weight_kg=payload.weight_kg,
            )
        )
    except EmailAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    except InvalidRoleAssignment:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Role cannot be assigned",
        )

    return UserRead.model_validate(user)

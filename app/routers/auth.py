from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.dependencies import get_current_user, get_db, require_admin
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registers a new user account.

    The first registered user is automatically designated as an 'admin';
    subsequent users are registered with the 'user' role.
    """
    is_first_user = db.query(models.User).count() == 0
    role = "admin" if is_first_user else "user"

    user = models.User(
        username=user_in.username.strip(),
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name.strip() if user_in.full_name else None,
        role=role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        ) from None
    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=schemas.Token,
    summary="Authenticate and receive JWT access token",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticates credentials and returns a signed JWT access token."""
    user = (
        db.query(models.User)
        .filter(models.User.username == form_data.username.strip())
        .first()
    )
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",  # nosec B106
        role=user.role,
        username=user.username,
    )


@router.get(
    "/me",
    response_model=schemas.UserOut,
    summary="Get current user details",
)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Returns the profile of the currently authenticated user."""
    return current_user


@router.get(
    "/users",
    response_model=list[schemas.UserOut],
    summary="List all users (Admin only)",
)
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    """Admin-only endpoint to list all registered users."""
    return db.query(models.User).offset(skip).limit(limit).all()

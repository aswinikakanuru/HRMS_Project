from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database import get_session
from schemas.user import UserCreate, UserResponse
from schemas.auth import LoginRequest, TokenResponse
from services.auth_service import register_user, login_user
from dependencies.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

# User Registration API
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    try:
        new_user = register_user(session=session, user_data=user_data)
        return new_user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except IntegrityError as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint error: {str(e.orig)}"
        )
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e.orig)}"
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

# User Login API 
@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    try:
        
        token = login_user(session, form_data.username, form_data.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return token

# User Login API via JSON 
@router.post("/login-json", response_model=TokenResponse)
def login_json(
    login_data: LoginRequest,
    session: Session = Depends(get_session)
):
    try:
        token = login_user(session, login_data.email, login_data.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    return token

# Get Current Logged-in User
@router.get("/getuser", response_model=UserResponse)
def get_user(current_user: User = Depends(get_current_user)):
    return current_user

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from jose import jwt, JWTError

from database import get_session
from models.user import User
from models.employee import Employee
from config import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user_id = int(user_id)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()

    if user is None or not user.is_active:
        raise credentials_exception

    return user

# Role-Based Access Control (RBAC) Dependency Factory
def require_roles(allowed_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Requires role: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

# Helper to automatically resolve logged-in User -> Employee record
def get_current_employee(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Employee:
    statement = select(Employee).where(Employee.user_id == current_user.id)
    employee = session.exec(statement).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No employee profile linked to this user account."
        )
    return employee

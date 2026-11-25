from datetime import datetime, date, timedelta, timezone
from sqlmodel import Session, select
import bcrypt
from jose import jwt

from models.user import User
from models.employee import Employee
from models.department import Department
from models.designation import Designation
from models.shift import Shift
from schemas.user import UserCreate
from schemas.auth import TokenResponse
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def register_user(session: Session, user_data: UserCreate):
    clean_email = user_data.email.strip().lower()
    statement = select(User).where(User.email == clean_email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise ValueError("Email already registered")

    hashed = hash_password(user_data.password)
    allowed_roles = ["Employee", "Manager", "HR", "Admin", "Leadership"]
    user_role = user_data.role if user_data.role in allowed_roles else "Employee"
    leadership_title = user_data.leadership_title if user_role == "Leadership" else None

    new_user = User(
        name=user_data.name.strip(),
        email=clean_email,
        hashed_password=hashed,
        role=user_role,
        leadership_title=leadership_title,
        is_active=True
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    dept = session.exec(select(Department)).first()
    if not dept:
        dept = Department(name="Engineering", description="Engineering Department")
        session.add(dept)
        session.commit()
        session.refresh(dept)

    desig = session.exec(select(Designation)).first()
    if not desig:
        desig = Designation(title="Software Engineer", department_id=dept.id, description="Staff Role")
        session.add(desig)
        session.commit()
        session.refresh(desig)

    gs = session.exec(select(Shift).where(Shift.code == "GS")).first()

    names = new_user.name.split(maxsplit=1)
    firstname = names[0]
    lastname = names[1] if len(names) > 1 else ""

    emp = Employee(
        employee_code=f"EMP-{1000 + new_user.id}",
        user_id=new_user.id,
        firstname=firstname,
        lastname=lastname,
        email=new_user.email,
        joining_date=date.today(),
        department_id=dept.id,
        designation_id=desig.id,
        shift_id=gs.id if gs else None,
        employee_status="active"
    )
    session.add(emp)
    session.commit()
    session.refresh(emp)

    return new_user


def login_user(session: Session, email: str, password: str):
    clean_email = email.strip().lower()
    statement = select(User).where(User.email == clean_email)
    user = session.exec(statement).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None

    emp = session.exec(select(Employee).where(Employee.user_id == user.id)).first()
    if not emp:
        emp_by_email = session.exec(select(Employee).where(Employee.email == user.email)).first()
        if emp_by_email:
            emp_by_email.user_id = user.id
            session.add(emp_by_email)
            session.commit()
        else:
            dept = session.exec(select(Department)).first()
            if not dept:
                dept = Department(name="Engineering", description="Engineering Department")
                session.add(dept)
                session.commit()
                session.refresh(dept)

            desig = session.exec(select(Designation)).first()
            if not desig:
                desig = Designation(title="Software Engineer", department_id=dept.id)
                session.add(desig)
                session.commit()
                session.refresh(desig)

            gs = session.exec(select(Shift).where(Shift.code == "GS")).first()

            names = user.name.split(maxsplit=1)
            emp = Employee(
                employee_code=f"EMP-{1000 + user.id}",
                user_id=user.id,
                firstname=names[0],
                lastname=names[1] if len(names) > 1 else "",
                email=user.email,
                joining_date=date.today(),
                department_id=dept.id,
                designation_id=desig.id,
                shift_id=gs.id if gs else None,
                employee_status="active"
            )
            session.add(emp)
            session.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token, token_type="bearer")

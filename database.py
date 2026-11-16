from sqlmodel import SQLModel, create_engine, Session
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)

def create_db_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

def check_db_connection():
    try:
        with Session(engine) as session:
            session.connection()
        print("PostgreSQL connected successfully.")
    except Exception as e:
        print("Database connection failed:", e)
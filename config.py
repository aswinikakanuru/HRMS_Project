import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


raw_expiry = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
ACCESS_TOKEN_EXPIRE_MINUTES = int(raw_expiry)

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not configured in .env")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not configured in .env")

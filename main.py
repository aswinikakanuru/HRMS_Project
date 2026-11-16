from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models  # Ensures all SQLModel tables are registered in metadata
from database import create_db_tables, check_db_connection

# Routers
from routers.auth import router as auth_router
from routers.department import router as department_router
from routers.designation import router as designation_router
from routers.employee import router as employee_router
from routers.attendance import router as attendance_router
from routers.leave import router as leave_router
from routers.wfh import router as wfh_router
from routers.notification import router as notification_router
from routers.dashboard import router as dashboard_router
from routers.holiday import router as holiday_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify DB connection and create all tables in PostgreSQL
    check_db_connection()
    create_db_tables()
    yield

app = FastAPI(
    title="HRMS - Human Resource Management System",
    description="Enterprise HRMS Backend API built with FastAPI, SQLModel & PostgreSQL",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware (Allows frontend apps like React, Angular, Vue to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register All API Routers
app.include_router(auth_router)
app.include_router(department_router)
app.include_router(designation_router)
app.include_router(employee_router)
app.include_router(attendance_router)
app.include_router(leave_router)
app.include_router(wfh_router)
app.include_router(notification_router)
app.include_router(dashboard_router)
app.include_router(holiday_router)

@app.get("/")
def home():
    return {
        "message": "Welcome to HRMS Portal API",
        "status": "online",
        "docs": "/docs"
    }

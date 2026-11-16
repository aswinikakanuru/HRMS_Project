"""
Standalone Database Connection & Table Health Check Script
Run with: python testdb.py
"""
from sqlmodel import Session, select, func
from database import engine, check_db_connection
from models.user import User
from models.department import Department
from models.designation import Designation
from models.employee import Employee
from models.attendance import Attendance
from models.leave_request import LeaveRequest
from models.holiday import Holiday

def run_health_check():
    print("=" * 50)
    print("HRMS DATABASE HEALTH CHECK")
    print("=" * 50)
    check_db_connection()

    with Session(engine) as session:
        users_count = session.exec(select(func.count(User.id))).one()
        dept_count = session.exec(select(func.count(Department.id))).one()
        desig_count = session.exec(select(func.count(Designation.id))).one()
        emp_count = session.exec(select(func.count(Employee.id))).one()
        att_count = session.exec(select(func.count(Attendance.id))).one()
        leave_count = session.exec(select(func.count(LeaveRequest.id))).one()
        holiday_count = session.exec(select(func.count(Holiday.id))).one()

        print(f"Users registered:       {users_count}")
        print(f"Departments:            {dept_count}")
        print(f"Designations:           {desig_count}")
        print(f"Employees onboarded:    {emp_count}")
        print(f"Attendance logs:        {att_count}")
        print(f"Leave requests:         {leave_count}")
        print(f"Holidays scheduled:     {holiday_count}")
    print("=" * 50)
    print("Status: All tables accessible and healthy!")
    print("=" * 50)

if __name__ == "__main__":
    run_health_check()

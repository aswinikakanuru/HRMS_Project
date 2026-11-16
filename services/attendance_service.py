from sqlmodel import Session, select
from datetime import date, datetime, timezone
import csv
import io
from fastapi import HTTPException, status
from fastapi.responses import Response
from models.attendance import Attendance

def clock_in(session: Session, employee_id: int) -> dict:
    today = date.today()
    now_utc = datetime.now(timezone.utc)

    statement = select(Attendance).where(
        Attendance.employee_id == employee_id,
        Attendance.attendance_date == today
    )
    attendance = session.exec(statement).first()

    if attendance and attendance.check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Already clocked in today at {attendance.check_in.strftime('%H:%M:%S')} UTC"
        )

    if not attendance:
        attendance = Attendance(
            employee_id=employee_id,
            attendance_date=today,
            check_in=now_utc,
            status="present"
        )
        session.add(attendance)
    else:
        attendance.check_in = now_utc
        attendance.status = "present"

    session.commit()
    session.refresh(attendance)
    return {"action": "CLOCK_IN_SUCCESS", "attendance": attendance}

def clock_out(session: Session, employee_id: int) -> dict:
    today = date.today()
    now_utc = datetime.now(timezone.utc)

    statement = select(Attendance).where(
        Attendance.employee_id == employee_id,
        Attendance.attendance_date == today
    )
    attendance = session.exec(statement).first()

    if not attendance or not attendance.check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot clock out without clocking in first today."
        )

    attendance.check_out = now_utc
    duration_hours = (attendance.check_out - attendance.check_in).total_seconds() / 3600
    if duration_hours < 4:
        attendance.remarks = f"Half Day ({duration_hours:.1f} hrs)"
    else:
        attendance.remarks = f"Full Day ({duration_hours:.1f} hrs)"

    session.commit()
    session.refresh(attendance)
    return {"action": "CLOCK_OUT_SUCCESS", "attendance": attendance}

def get_today_attendance(session: Session, employee_id: int) -> Attendance:
    today = date.today()
    statement = select(Attendance).where(
        Attendance.employee_id == employee_id,
        Attendance.attendance_date == today
    )
    attendance = session.exec(statement).first()
    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not clocked in today")
    return attendance

def get_my_attendance_history(session: Session, employee_id: int) -> list[Attendance]:
    statement = (
        select(Attendance)
        .where(Attendance.employee_id == employee_id)
        .order_by(Attendance.attendance_date.desc())
    )
    return session.exec(statement).all()

def export_attendance_csv(session: Session) -> Response:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Record ID", "Employee ID", "Date", "Check In (UTC)", "Check Out (UTC)", "Status", "Remarks"])

    records = session.exec(select(Attendance).order_by(Attendance.attendance_date.desc())).all()
    for r in records:
        writer.writerow([
            r.id,
            r.employee_id,
            r.attendance_date,
            r.check_in.strftime("%Y-%m-%d %H:%M:%S") if r.check_in else "",
            r.check_out.strftime("%Y-%m-%d %H:%M:%S") if r.check_out else "",
            r.status,
            r.remarks or ""
        ])

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance_report.csv"}
    )

from sqlalchemy import inspect, text
from sqlmodel import SQLModel, create_engine, Session, select
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)


def migrate_postgres_schema():
    """Idempotently add new columns to existing PostgreSQL/SQLite tables without dropping data."""
    inspector = inspect(engine)
    migrations = {
        "users": {
            "leadership_title": "VARCHAR(100)",
        },
        "employees": {
            "shift_id": "INTEGER REFERENCES shifts(id)",
        },
        "attendance": {
            "shift_id": "INTEGER REFERENCES shifts(id)",
            "work_hours": "DOUBLE PRECISION NOT NULL DEFAULT 0.0",
            "is_late": "BOOLEAN NOT NULL DEFAULT FALSE",
            "late_minutes": "INTEGER NOT NULL DEFAULT 0",
            "is_early_out": "BOOLEAN NOT NULL DEFAULT FALSE",
            "early_out_minutes": "INTEGER NOT NULL DEFAULT 0",
            "detected_ot_hours": "DOUBLE PRECISION NOT NULL DEFAULT 0.0",
            "overtime_hours": "DOUBLE PRECISION NOT NULL DEFAULT 0.0",
            "ot_approved": "BOOLEAN NOT NULL DEFAULT FALSE",
            "deduction_reason": "VARCHAR(255)",
            "is_regularised": "BOOLEAN NOT NULL DEFAULT FALSE",
            "regularisation_remarks": "VARCHAR(255)",
        },
        "leave_requests": {
            "manager_status": "VARCHAR(30) NOT NULL DEFAULT 'pending'",
            "manager_comments": "TEXT",
            "hr_status": "VARCHAR(30) NOT NULL DEFAULT 'pending'",
            "hr_comments": "TEXT",
            "leadership_status": "VARCHAR(30) NOT NULL DEFAULT 'skipped'",
            "leadership_comments": "TEXT",
        },
        "wfh_requests": {
            "manager_status": "VARCHAR(30) NOT NULL DEFAULT 'pending'",
            "manager_comments": "TEXT",
            "hr_status": "VARCHAR(30) NOT NULL DEFAULT 'pending'",
            "hr_comments": "TEXT",
            "leadership_status": "VARCHAR(30) NOT NULL DEFAULT 'skipped'",
            "leadership_comments": "TEXT",
        },
    }

    with engine.begin() as conn:
        for table, cols in migrations.items():
            if not inspector.has_table(table):
                continue
            existing = {c["name"] for c in inspector.get_columns(table)}
            for col_name, col_def in cols.items():
                if col_name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"))


def seed_initial_shifts():
    """Ensure base shift definitions exist without creating unwanted demo users."""
    from models.shift import Shift
    from models.employee import Employee

    with Session(engine) as session:
        default_shifts = [
            Shift(
                name="General Shift",
                code="GS",
                start_time="09:00",
                end_time="18:00",
                grace_period_mins=15,
                late_half_day_threshold_mins=60,
                early_out_half_day_threshold_mins=60,
                half_day_threshold_hours=4.5,
                full_day_hours=9.0,
                is_rotational=False,
                description="Standard 9 AM - 6 PM day shift.",
            ),
            Shift(
                name="Morning Shift",
                code="MS",
                start_time="08:00",
                end_time="17:00",
                grace_period_mins=15,
                late_half_day_threshold_mins=60,
                early_out_half_day_threshold_mins=60,
                half_day_threshold_hours=4.5,
                full_day_hours=9.0,
                is_rotational=False,
                description="Early Morning 8 AM - 5 PM shift.",
            ),
            Shift(
                name="Evening Shift",
                code="ES",
                start_time="14:00",
                end_time="23:00",
                grace_period_mins=15,
                late_half_day_threshold_mins=60,
                early_out_half_day_threshold_mins=60,
                half_day_threshold_hours=4.5,
                full_day_hours=9.0,
                is_rotational=False,
                description="Evening 2 PM - 11 PM shift.",
            ),
            Shift(
                name="Night Shift",
                code="NS",
                start_time="22:00",
                end_time="07:00",
                grace_period_mins=15,
                late_half_day_threshold_mins=60,
                early_out_half_day_threshold_mins=60,
                half_day_threshold_hours=4.5,
                full_day_hours=9.0,
                is_rotational=False,
                description="Overnight 10 PM - 7 AM shift.",
            ),
            Shift(
                name="Rotational Shift",
                code="RS",
                start_time="08:00",
                end_time="17:00",
                grace_period_mins=15,
                late_half_day_threshold_mins=60,
                early_out_half_day_threshold_mins=60,
                half_day_threshold_hours=4.5,
                full_day_hours=9.0,
                is_rotational=True,
                rotation_pattern="Morning -> Evening -> Night Weekly",
                description="Weekly rotational shift.",
            ),
        ]
        for s in default_shifts:
            if not session.exec(select(Shift).where(Shift.code == s.code)).first():
                session.add(s)
        session.commit()

        gs_shift = session.exec(select(Shift).where(Shift.code == "GS")).first()
        if gs_shift:
            for emp in session.exec(select(Employee).where(Employee.shift_id == None)).all():
                emp.shift_id = gs_shift.id
                session.add(emp)
            session.commit()


def seed_org_catalog():
    """Ensure all standard departments and department-specific designations (incl. Team Lead & Intern) exist."""
    from models.department import Department
    from models.designation import Designation
    from models.employee import Employee

    org_catalog = [
        ("Development", "Software & product engineering", [
            "Software Engineer",
            "Senior Software Engineer",
            "Frontend Developer",
            "Backend Developer",
            "Full Stack Developer",
            "Team Lead",
            "Engineering Manager",
            "Intern",
        ]),
        ("Testing", "Quality assurance & software testing", [
            "QA Engineer",
            "Senior QA Engineer",
            "Automation Test Engineer",
            "Team Lead",
            "QA Manager",
            "Intern",
        ]),
        ("Marketing", "Brand, digital & growth marketing", [
            "Marketing Associate",
            "Digital Marketing Executive",
            "Content Strategist",
            "Team Lead",
            "Marketing Manager",
            "Intern",
        ]),
        ("Talent Acquisition", "Recruitment & talent hiring", [
            "Talent Acquisition Specialist",
            "Technical Recruiter",
            "Senior Recruiter",
            "Team Lead",
            "Talent Acquisition Manager",
            "Intern",
        ]),
        ("Business Development", "Client partnerships & revenue growth", [
            "Business Development Associate",
            "Business Development Executive",
            "Account Executive",
            "Team Lead",
            "Business Development Manager",
            "Intern",
        ]),
        ("DevOps", "Cloud infrastructure, CI/CD & reliability", [
            "DevOps Engineer",
            "Senior DevOps Engineer",
            "Site Reliability Engineer",
            "Cloud Engineer",
            "Team Lead",
            "DevOps Manager",
            "Intern",
        ]),
        ("HR", "Human resources & people operations", [
            "HR Executive",
            "HR Generalist",
            "HR Business Partner",
            "HR Lead",
            "HR Manager",
            "Intern",
        ]),
        ("IT", "Corporate IT systems & support", [
            "IT Support Engineer",
            "IT Systems Engineer",
            "Network Administrator",
            "IT Lead",
            "IT Manager",
            "Intern",
        ]),
        ("Executive Leadership", "C-suite & Directors", [
            "Chief Executive Officer",
            "Director",
        ]),
    ]

    with Session(engine) as session:
        # Normalize legacy department names cleanly without breaking foreign keys
        eng_dept = session.exec(select(Department).where(Department.name == "Engineering")).first()
        dev_dept = session.exec(select(Department).where(Department.name == "Development")).first()
        if eng_dept and not dev_dept:
            eng_dept.name = "Development"
            eng_dept.description = "Software & product engineering"
            session.add(eng_dept)
            session.commit()

        hr_full = session.exec(select(Department).where(Department.name == "Human Resources")).first()
        hr_short = session.exec(select(Department).where(Department.name == "HR")).first()
        if hr_full and not hr_short:
            hr_full.name = "HR"
            hr_full.description = "Human resources & people operations"
            session.add(hr_full)
            session.commit()

        dept_by_name = {d.name: d for d in session.exec(select(Department)).all()}
        for dept_name, dept_desc, titles in org_catalog:
            dept = dept_by_name.get(dept_name)
            if not dept:
                dept = Department(name=dept_name, description=dept_desc)
                session.add(dept)
                session.commit()
                session.refresh(dept)
                dept_by_name[dept_name] = dept

        # Fix historical IT Lead mapped to dept 1 -> move to IT department if IT exists
        it_dept = dept_by_name.get("IT")
        if it_dept:
            misplaced_it_lead = session.exec(
                select(Designation).where(Designation.title == "IT Lead", Designation.department_id != it_dept.id)
            ).first()
            if misplaced_it_lead:
                existing_it_lead = session.exec(
                    select(Designation).where(Designation.title == "IT Lead", Designation.department_id == it_dept.id)
                ).first()
                if not existing_it_lead:
                    misplaced_it_lead.department_id = it_dept.id
                    session.add(misplaced_it_lead)
                    session.commit()

        # Deduplicate designations within the same (department_id, title) safely
        all_desigs = session.exec(select(Designation).order_by(Designation.id)).all()
        seen_keys: dict[tuple, int] = {}
        for g in all_desigs:
            key = (g.department_id, (g.title or "").strip().lower())
            if key in seen_keys:
                canonical_id = seen_keys[key]
                for emp in session.exec(select(Employee).where(Employee.designation_id == g.id)).all():
                    emp.designation_id = canonical_id
                    session.add(emp)
                session.commit()
                session.delete(g)
                session.commit()
            else:
                seen_keys[key] = g.id

        # Seed missing designations per department
        for dept_name, _, titles in org_catalog:
            dept = dept_by_name[dept_name]
            existing_titles = {
                (g.title or "").strip().lower()
                for g in session.exec(select(Designation).where(Designation.department_id == dept.id)).all()
            }
            for title in titles:
                if title.lower() not in existing_titles:
                    session.add(Designation(title=title, department_id=dept.id))
                    existing_titles.add(title.lower())
        session.commit()


def create_db_tables():
    SQLModel.metadata.create_all(engine)
    migrate_postgres_schema()
    seed_initial_shifts()
    seed_org_catalog()


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

import sqlite3
from contextlib import closing
from datetime import date

import streamlit as st

from database import DATABASE_PATH, get_follow_up_reminders, initialize_database

APPLICATION_STATUSES = [
    "Applied",
    "Shortlisted",
    "Interview Scheduled",
    "Selected",
    "Rejected",
]

initialize_database()


def get_applications():
    """Return all applications as dictionaries for the Streamlit table."""
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        cursor = connection.execute("""
            SELECT application_id, company_name, job_role, application_date, status,
                   follow_up_date
            FROM applications
            ORDER BY application_id
        """)
        column_names = [column[0] for column in cursor.description]
        return [dict(zip(column_names, row)) for row in cursor.fetchall()]


def get_total_applications():
    """Return the number of application records in the database."""
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        result = connection.execute(
            "SELECT COUNT(*) FROM applications"
        ).fetchone()
        return result[0]


def get_most_applied_role():
    """Return the most applied-for role, breaking ties alphabetically."""
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        result = connection.execute("""
            SELECT job_role, COUNT(*) AS application_count
            FROM applications
            GROUP BY job_role
            ORDER BY application_count DESC, job_role COLLATE NOCASE ASC
            LIMIT 1
        """).fetchone()
        return result[0] if result else None


def get_status_counts():
    """Return application counts for each status, including statuses with zero."""
    counts = {status: 0 for status in APPLICATION_STATUSES}

    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        rows = connection.execute("""
            SELECT status, COUNT(*)
            FROM applications
            GROUP BY status
        """).fetchall()

    for status, count in rows:
        # Include any status that may already exist in the database.
        label = status if status else "No status"
        counts[label] = count

    return counts


st.set_page_config(page_title="Placement Application Tracker", page_icon="📋")
st.title("Placement Application Tracker")
st.write("Keep track of your job applications in one place.")

st.header("Add Application")

# A form submits all application details together when its button is clicked.
with st.form("add_application_form"):
    company_name = st.text_input("Company Name")
    job_role = st.text_input("Job Role")
    application_date = st.date_input("Application Date", value=date.today())
    status = st.selectbox("Status", APPLICATION_STATUSES)
    has_follow_up_date = st.checkbox("Set a follow-up date")
    follow_up_date = (
        st.date_input("Follow-up Date", value=date.today())
        if has_follow_up_date
        else None
    )
    submitted = st.form_submit_button("Add Application")

if submitted:
    # Do not save an application without a company name and job role.
    if not company_name.strip():
        st.error("Please enter a Company Name.")
    elif not job_role.strip():
        st.error("Please enter a Job Role.")
    else:
        # Save the date as text in YYYY-MM-DD format.
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            with connection:
                connection.execute("""
                    INSERT INTO applications
                        (company_name, job_role, application_date, status, follow_up_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    company_name.strip(),
                    job_role.strip(),
                    application_date.isoformat(),
                    status,
                    follow_up_date.isoformat() if follow_up_date else None,
                ))
        st.success("Application added successfully.")

st.header("Application Summary")
total_applications = get_total_applications()
most_applied_role = get_most_applied_role()

summary_columns = st.columns(2)
summary_columns[0].metric("Total Applications", total_applications)
summary_columns[1].metric(
    "Most Applied Role",
    most_applied_role if most_applied_role else "No applications yet",
)

st.subheader("Status-wise Summary")
status_counts = get_status_counts()
st.bar_chart(status_counts)

st.subheader("Follow-up Reminders")
follow_up_reminders = get_follow_up_reminders()
reminder_columns = st.columns(2)
for column, label, category in (
    (reminder_columns[0], "Overdue", "overdue"),
    (reminder_columns[1], "Due today or in the next 7 days", "upcoming"),
):
    with column:
        st.markdown(f"**{label}**")
        reminders = follow_up_reminders[category]
        if reminders:
            st.dataframe(reminders, use_container_width=True, hide_index=True)
        else:
            st.caption("No follow-ups in this period.")

st.header("View Applications")
applications = get_applications()

if applications:
    st.dataframe(applications, use_container_width=True, hide_index=True)
else:
    st.info("No applications are available yet. Add one using the form above.")

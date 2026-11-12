# Placement Application Tracker

A Streamlit app for recording job applications and summarizing them by role and status.
Applications can also have an optional follow-up date. The dashboard highlights
overdue follow-ups and those due today or within the next seven days.

## Run locally

From this folder, install the dependency and start the app:

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

To create a fresh database, run `python init_db.py` from this folder. The app reads
and writes `placements.db` next to `app.py`. The app adds the follow-up date column
to an existing database automatically, preserving its current application records.

## Data note

The committed `placements.db` contains existing application records. This is a
public repository, so anyone can access that data. Remove or replace the database
before publishing if those records should not be public.
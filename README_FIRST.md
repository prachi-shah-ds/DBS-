# Phase 1 + 2 starter files — read this first

## One thing you must do by hand
Open your repo's `requirements.txt` and add this line (if it's not already there):

```
jsonschema>=4.0.0
```

This can't be auto-merged like the other files since requirements.txt already exists in your repo — just open it in VS Code and add the line yourself, then save.

## Everything else
All other files/folders in this package can be copied straight into the root of your Jodo repo, the same way you did with the person5_starter files:

- auth/routes.py
- dashboard/routes.py
- docs/schemas/dashboard_layout.schema.json
- templates/base.html
- templates/login.html
- templates/dashboard.html
- alembic/versions/0002_add_dashboard_layout.py

## Important: check the migration file
`alembic/versions/0002_add_dashboard_layout.py` has a placeholder:

```
down_revision = '<previous>'
```

You need to replace `<previous>` with the actual revision ID of your current latest migration (likely `0001_add_audit_logs` if you added that one earlier). If you're unsure, you can skip alembic entirely and just run `python seed.py`, which creates all tables directly — no migration needed for local testing.

## After copying the files in
1. Add the jsonschema line to requirements.txt (see above).
2. Fix the down_revision in the migration file (or skip alembic and just run seed.py).
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python seed.py` (creates tables + seed data)
5. Run the app: `python app.py`
6. Open http://127.0.0.1:5000/login — login with admin@example.com / passw0rd

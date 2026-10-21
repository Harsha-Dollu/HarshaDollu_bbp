# Boston Bioprocess Take-Home

Desktop proof of concept for batch scheduling and one-vessel closed-loop bioreactor control.

## Local run

Backend (PowerShell, `backend`): `..\.venv\Scripts\Activate.ps1` then `uvicorn app.main:app --reload --port 8000`.

Frontend (PowerShell, `frontend`): `ng serve --open`.

Open `http://localhost:4200`. Start a clean replay with `POST /api/simulator/reset` followed by `POST /api/simulator/start`.

## How I split and evaluated the forecaster

The supplied CSVs are used directly. A Ridge multi-output regression consumes the preceding 60 process-minutes of DO and feed rate and predicts DO for the next 10 minutes. Runs A and B are training data; run C is a complete chronological held-out test run, so windows never cross runs or leak future readings.

| Model | MAE (%DO) | RMSE (%DO) |
|---|---:|---:|
| Ridge | 0.493 | 0.896 |
| Persistence baseline | 0.576 | 1.062 |

## Decisions and trade-offs

- SQLite and SQLAlchemy keep this proof of concept local and simple; a production deployment would use PostgreSQL and migrations.
- Invalid scheduling writes are rejected with HTTP 422 and readable violation details, preserving the backend as the source of truth. Seeded data deliberately contains Alpha Seed/Beta Seed equipment overlap and Alpha Seed/Alpha Bioreactor sequencing violations.
- The controller is transparent and rule based. It runs every five simulated minutes after a 60-minute history exists, honours command validation and five-minute actuator lag, but is not a validated production control policy.

## How I would deploy, retrain and monitor this

Deploy the Angular build behind a static host and FastAPI behind an authenticated API gateway, with PostgreSQL, migrations, structured logs, metrics, backups, and role-based access. Retrain offline on approved historical runs, version models and evaluation datasets, then promote only after held-out and shadow-mode checks. Monitor reading latency, missing signals, command rejections, model error after observations arrive, and DO safety excursions; alert and fall back to manual control on anomalies.

## Seed data and demo

Scheduling seed data has three batches across five equipment lanes. The simulator replays `data_kit/run_A.csv`; process time advances one minute per wall-clock second. A demo should show the Gantt violations, an edit that resolves one violation, then reset/start the simulator, wait one minute, and show automatic forecast/controller activity.

## Hosting and recording

Hosted URL: not deployed yet. Screen recording: not recorded yet.

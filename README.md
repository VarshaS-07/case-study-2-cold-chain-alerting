# Nimbus Freight — Cold-Chain Alerting Engine

A hackathon prototype for monitoring refrigerated-truck sensor readings, detecting **sustained temperature violations**, highlighting **potential upcoming breaches**, and presenting fleet conditions through an authenticated dashboard.


## Problem

A temperature reading above the safe limit should not automatically generate an alert: isolated spikes create alert fatigue. Nimbus Freight needs to identify sustained unsafe conditions, explain the evidence, and avoid repeatedly alerting on the same incident.

## Implemented features

- **Historical data processing:** validate, sort, group and deduplicate sensor readings by truck.
- **Sustained violation detection:** temperatures **strictly above 8°C** for **20 continuous minutes**; gaps greater than **7 minutes** interrupt continuity.
- **Predictive warning:** a simple linear trend over the last **three consecutive rising readings** estimates whether the temperature could reach 8°C within **10 minutes**. This is a heuristic, not a machine-learning forecast.
- **Incident deduplication:** stable incident keys and database checks prevent duplicate incidents on repeated analysis.
- **Admin authentication:** username/password, email OTP and authenticated API access.
- **Email notifications:** SMTP-based alert delivery with notification audit records.
- **React dashboard:** fleet summary, truck temperatures and trends, incident history, data-quality gaps, notification records and a separate predictive-warning demonstration.
- **Synthetic predictive demo:** `DEMO-01` shows readings of 5°C, 6°C and 7°C five minutes apart, giving a warming rate of 0.2°C/min and a predicted 5-minute ETA. The demo is labeled synthetic and does not alter the provided dataset.

## Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Recharts |
| Backend | Python, FastAPI, SQLAlchemy, Uvicorn |
| Database | SQLite |
| Authentication | Password hashing, email OTP, JWT |
| Notifications | SMTP email; Azure Logic Apps integration is optional/pending verification |
| Tests | pytest |

## Repository structure

```text
backend/
  api/                 # Fleet, readings, incidents and analytics endpoints
  auth/                # Admin initialization, login, OTP and token logic
  engine/              # Preprocessing, violation detection, prediction
  notifications/       # Email and optional Azure workflow integration
  database.py          # SQLAlchemy database setup
  main.py              # FastAPI application
  run_analysis.py      # Historical dataset processing
  demo_prediction.py   # Synthetic predictive-warning demonstration
frontend/
  src/                 # React dashboard and API client
starter_kit/data/      # Original sensor dataset and demo fixture
tests/                 # Engine tests
requirements.txt
SOLUTION_DESIGN.md     # Architecture, assumptions and trade-offs
```

## Run locally

**Requirements:** Python 3.12+ and a compatible Node.js version (Node 22 recommended for this frontend).

From the repository root, create and activate a Python environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a **local** `.env` file in the repository root. Do not commit it. Configure the variables used by `backend/config.py`:

```dotenv
ADMIN_USERNAME=admin
ADMIN_EMAIL=your-email@example.com
ADMIN_PASSWORD=choose-a-long-unique-password
AUTH_SECRET=generate-a-random-secret
ALERT_EMAIL=your-email@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-new-app-password
SMTP_FROM=your-email@example.com
```

For Gmail, use an appropriate Gmail App Password rather than your regular account password. **Never paste secrets into issues, commits or documentation.**

Initialize the admin account and process the provided dataset:

```powershell
python -m backend.auth.init_admin
python -m backend.run_analysis
```

Start the API:

```powershell
python -m uvicorn backend.main:app --reload
```

API documentation: **http://127.0.0.1:8000/docs**

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite (typically **http://localhost:5173**). Sign in with the configured admin credentials and the emailed OTP.

**Note:** The current `backend/database.py` version may store SQLite at `backend/coldchain.db` and override `DATABASE_URL`. If so, configure the database path in that file before attempting cloud deployment; simply setting `DATABASE_URL` will not change the path. Local startup does not require Gunicorn; Gunicorn is for Linux deployments.

## Expected results from the supplied dataset

| Measure | Expected result |
|---|---:|
| Trucks | 5 |
| Valid historical readings | 54 |
| Confirmed sustained violations | 2 (T-01 and T-05) |
| Predictive warnings in historical dataset | 0 |
| Data-quality issue | T-04 has a 10-minute reporting gap |

The absence of predictive warnings in the original dataset is expected. Use the separate `DEMO-01` fixture to demonstrate prediction without misrepresenting historical results.

## API overview

- `/docs` — interactive API documentation
- `/auth/login` — first authentication step
- `/auth/verify-otp` — verify emailed OTP
- `/auth/me` — authenticated admin details
- `/api/summary` — fleet overview
- `/api/trucks` — truck list and status
- `/api/trucks/{truck_id}/readings` — temperature history
- `/api/incidents` — detected incidents
- `/api/gaps` — missing-data gaps
- `/api/notifications` — notification audit
- `/api/demo/predictive-warning` — isolated synthetic prediction example

Dashboard API routes require authentication. Refer to `/docs` for request and response schemas.

## Tests

```powershell
python -m pytest -q
```

## Deployment notes

The frontend and backend can be hosted separately, for example with **Vercel** for the Vite frontend and **Render** for FastAPI. These services are **not assumed deployed** merely because configuration steps are documented.

- Backend start command for Render (from repository root):

  ```bash
  uvicorn backend.main:app --host 0.0.0.0 --port $PORT
  ```

- Frontend production builds should use `VITE_API_BASE_URL` to point to the deployed backend, **provided `frontend/src/api.js` has been updated to read that variable**.
- The backend must allow the frontend origin in its CORS configuration.
- Admin creation and dataset processing must run against the deployed database before login and analytics will work. The local commands above do **not** run automatically on Render unless startup initialization is configured.
- **Render Free has an ephemeral filesystem**. SQLite state, including OTPs and notification history, can disappear on restart/redeploy. Use a persistent database for production.
- Azure Logic Apps requires a separately deployed workflow, a configured callback URL and an actual backend integration; having an `azure_sender.py` module alone does not prove workflow execution or SMS delivery.

## Known limitations and future work

- Processes a **static historical dataset**, not real-time sensor streams.
- The prediction is an explainable linear extrapolation, sensitive to noisy readings.
- A gap over seven minutes breaks continuity, potentially delaying confirmation.
- Single-admin authentication and SQLite are suitable for a prototype, not a large multi-tenant deployment.
- Delivery through external providers is dependent on credentials, connectivity and provider availability. SMS via Azure Logic Apps requires an additional eligible SMS provider and is **not claimed as working** unless tested.
- Future enhancements: live ingestion, configurable per-cargo thresholds, recovery/hysteresis rules, managed persistent storage, alert retries and monitoring.


# Nimbus Freight — Cold-Chain Alerting Engine
**Solution design | Hackathon v1 | 4 November 2026**

## 1. Problem and scope
Refrigerated trucks report temperature readings every few minutes. Alerting on every high reading creates noise; missing sustained excursions risks cargo damage. Our solution processes the **provided historical JSON dataset**, predicts approaching threshold breaches, confirms sustained violations, sends notifications, and shows explainable fleet analytics on a protected admin dashboard.

**Demo flow:** Admin opens the React website and signs in with username/password plus a **5-minute email OTP**. The operator starts the Python batch processor from a terminal. It reads the JSON, computes truck states and alerts, writes results to SQLite, triggers configured notification channels, and the dashboard polls FastAPI for updated results. This is **historical replay**, not live telematics.

## 2. Architecture
```text
 Admin browser (React + Vite + Tailwind + Recharts)
   |  login/password -> email OTP -> authenticated dashboard
   v
 FastAPI (auth, truck/analytics/incident/notification endpoints)
   |                                ^
   v                                |
 SQLite (users, OTPs, trucks, readings, incidents, notifications)
   ^                                ^
   |                                |
 Terminal: python run_analysis.py      Notification manager
   |                                ^         |                  |
 Static JSON -> validate/sort/dedup -> detection engine       |
                |                 |        SMTP email       Azure Logic Apps
                |                 |        (OTP + alerts)       |
                +-> trend / ETA --+                           SMS provider
                +-> sustained breach state machine             (e.g. ACS*)
```
*Azure Logic Apps orchestrates SMS; it is not itself an SMS carrier. Azure Communication Services (ACS) or another eligible SMS provider needs a provisioned sender, geographic eligibility and potentially paid usage. Provisioning and delivery must be verified; no guaranteed SMS delivery is assumed.*

**Separation of concerns:** The processing engine works without the web app or Azure. FastAPI reads persisted results; Logic Apps handles external workflow execution, while SQLite is the application source of truth. If Azure fails, dashboard processing and direct SMTP email continue; SMS is marked pending/failed, not sent.

## 3. Detection assumptions and alert rules
| Rule | Initial v1 policy |
|---|---|
| Upper safe temperature | **8°C** (starter utility default); high means `temperature > 8` |
| Confirmed violation | **20 minutes** continuously above threshold, measured by sensor timestamps |
| Expected reporting / gap | ~5 minutes; gap **>7 minutes** interrupts continuity and is flagged |
| Predictive warning | Last **3 consecutive valid readings** rising; estimated time to threshold **≤10 min**, while still safe |
| Recovery | First valid in-range reading ends a breach episode |
| Repeats | One warning and one critical event per truck episode; no repeat notifications on reruns |

For a consistently rising three-reading window: `rate = (T_latest - T_oldest) / elapsed_minutes` (°C/min). If `rate > 0` and `T_latest <= 8`, `ETA = (8 - T_latest) / rate`; warn for `0 < ETA <= 10`. This is **linear extrapolation**, not a guaranteed forecast. Group by truck and sort by sensor event time before processing; reject invalid records, handle duplicate timestamps deterministically, and never infer continuous unsafe temperature across a long missing-data gap. Input has no arrival timestamps, so actual network lateness cannot be assessed. A brief spike must not trigger a confirmed incident.

## 4. Authentication and security
A single seeded admin account is sufficient for v1; no signup or multi-role administration. Store **password hashes** (e.g. Argon2/bcrypt), never plaintext. After password validation, generate a cryptographically random 6-digit OTP and send it via **direct SMTP email**. Store only a keyed hash/digest of the OTP, with `expires_at = issued_at + 5 minutes`, a maximum of **5 attempts**, and one-time consumption. Limit OTP requests; on successful verification issue a short-lived authenticated session (prefer an HttpOnly, SameSite cookie), and protect all dashboard API endpoints. Store SMTP credentials, session secret and Logic Apps endpoint in `.env` (never commit secrets). This is a local hackathon implementation, not a production identity platform.

## 5. SQL database design (SQLite)
| Table | Core fields | Responsibility |
|---|---|---|
| `users` | `id`, `username` (unique), `password_hash`, `email`, `role` | Admin identity |
| `login_otps` | `id`, `user_id`, `otp_digest`, `expires_at`, `used_at`, `attempts` | OTP lifecycle |
| `trucks` | `truck_id` (PK), `threshold_c` | Truck configuration |
| `sensor_readings` | `id`, `truck_id`, `timestamp`, `temperature_c`, `humidity_pct` | Historical measurements; unique `(truck_id,timestamp)` |
| `incidents` | `id`, `truck_id`, `type`, `episode_key`, `started_at`, `detected_at`, `ended_at`, `status`, `reason` | Predictive warnings and sustained breaches |
| `notifications` | `id`, `incident_id`, `channel`, `recipient`, `status`, `attempt_count`, `provider_ref`, `last_error`, `sent_at` | Delivery state and deduplication |

**Relationships:** `login_otps.user_id → users.id`; `sensor_readings.truck_id → trucks.truck_id`; `incidents.truck_id → trucks.truck_id`; `notifications.incident_id → incidents.id`. Use a stable `episode_key` per truck/event episode and a uniqueness constraint on `(incident_id, channel, recipient)` to avoid duplicates. `notifications` records may progress through `pending → accepted/failed` and later `delivered` only if a provider receipt exists. If detailed retry auditing becomes necessary, add a `notification_attempts` table.

**Why SQL if using Logic Apps?** SQL persists the **business state** (sensor readings, incidents, user access and whether each alert has been attempted). Logic Apps executes the **delivery workflow**. A successful HTTP trigger does not prove SMS delivery. Store workflow/provider references and statuses; reconcile with downstream results where supported. Do not mark a message delivered solely because Logic Apps accepted a request.

## 6. Notification and dashboard behavior
| Event | Dashboard | Email (SMTP) | SMS (Azure Logic Apps) |
|---|---|---|---|
| Predicted breach | Amber warning, trend and ETA | Alert to admin | Trigger SMS workflow |
| Confirmed sustained breach | Red incident, elapsed duration and reason | Critical alert | Trigger SMS workflow |
| Ongoing same episode | Update chart/status | Suppress repeat | Suppress repeat |
| Recovery or missing-data gap | Resolved/data-quality indicator | None by default | None by default |

Dashboard shows summary cards, latest **observed** truck temperatures, above-threshold vs confirmed-incident states, temperature chart with threshold line, rate/ETA, incident history and email/SMS statuses. Poll API after batch execution. For historical data, use **dry-run notifications by default**; explicit `--send` enables delivery to approved test recipients. Persist event IDs and per-channel status before attempting sends; retries must not generate duplicate alerts.

## 7. Technology stack
| Layer | Technology | Why |
|---|---|---|
| UI | React, Vite, Tailwind CSS, Recharts | Lightweight admin dashboard and graphs |
| Backend/API | Python 3, FastAPI, Uvicorn | Reuses Python detection engine; protected JSON APIs |
| Storage | SQLite (`sqlite3`) | Small dataset, durable state, simple setup |
| Authentication | Password hashing, SMTP OTP, signed session | Minimal two-step admin login |
| Notifications | Python `smtplib` + Azure Logic Apps + eligible SMS provider | Email independent of Azure; automated cloud SMS workflow |
| Tests/config | pytest, `.env` | Repeatable tests and secret isolation |

## 8. Validation, trade-offs, demo and future work
**Test cases:** T-01 sustained breach; T-02 isolated spike; T-03 normal; T-04 gap handling; T-05 shuffled input. Also test warming vs cooling, OTP expiry/reuse/attempt limits, duplicate reruns, notification failures, and dashboard/API authorization. If the provided data lacks a clean predictive-warning example, use a **separately labeled synthetic fixture** rather than altering the supplied data.

**Trade-offs:** A conservative gap policy can miss an actual violation; a simple trend is interpretable but noisy. SQLite and one admin suit a hackathon, not a distributed enterprise fleet. External SMS depends on Azure/provider availability and cost. Static replay cannot claim real-time operation. Prioritize a working detection engine, protected dashboard and real SMTP email; demonstrate Azure workflow/SMS only after successful provisioning and testing.

**Demo:** Start API and frontend → login and verify 5-minute OTP → run `python run_analysis.py` → inspect trucks/analytics/incidents → show email and Azure workflow/SMS results where available → rerun to prove deduplication. **Future work:** streaming ingestion, configurable cargo thresholds, hysteresis, advanced forecasting, notification delivery callbacks, managed SQL, multi-admin RBAC, and production monitoring.

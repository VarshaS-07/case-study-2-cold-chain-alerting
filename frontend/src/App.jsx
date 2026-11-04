

import { useEffect, useState } from "react";
import Login from "./Login";
import { api, getToken, clearToken } from "./api";
import {
  Activity, AlertTriangle, Bell, Database,
  RefreshCw, Thermometer, Truck, WifiOff
} from "lucide-react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine
} from "recharts";
import "./App.css";

function formatTime(value) {
  if (!value) return "—";
  return value.replace("T", " ").slice(0, 16);
}

function StatCard({ icon: Icon, label, value, tone = "" }) {
  return (
    <div className={`stat-card ${tone}`}>
      <div className="stat-heading">
        <span>{label}</span>
        <Icon size={20} />
      </div>
      <div className="stat-value">{value ?? "—"}</div>
    </div>
  );
}

function Dashboard({ onLogout }) {
  const [summary, setSummary] = useState(null);
  const [trucks, setTrucks] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [gaps, setGaps] = useState([]);
  const [selectedTruck, setSelectedTruck] = useState("");
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notifications, setNotifications] = useState([]);
  const [demoData, setDemoData] = useState(null);
const [demoLoading, setDemoLoading] = useState(false);
const [demoError, setDemoError] = useState("");
  async function loadDashboard() {
    setLoading(true);
    setError("");

    try {
      const [summaryData, truckData, incidentData, gapData,notificationData] =
        await Promise.all([
          api.getSummary(),
          api.getTrucks(),
          api.getIncidents(),
          api.getGaps(),
          api.getNotifications(),
        ]);

      setSummary(summaryData);
      setTrucks(truckData);
      setIncidents(incidentData);
      setGaps(gapData);
      setNotifications(notificationData);
      setSelectedTruck((previous) =>
        truckData.some((truck) => truck.truck_id === previous)
          ? previous
          : (truckData[0]?.truck_id ?? "")
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    if (!selectedTruck) {
      setHistory(null);
      return;
    }

    let cancelled = false;
    setHistory(null);

    api.getReadings(selectedTruck)
      .then((data) => {
        if (!cancelled) setHistory(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedTruck]);

  async function runPredictiveDemo() {
    setDemoLoading(true);
    setDemoError("");
  
    try {
      const data = await api.getPredictiveDemo();
      setDemoData(data);
    } catch (err) {
      setDemoError(err.message);
    } finally {
      setDemoLoading(false);
    }
  }

  const chartData = (history?.readings ?? []).map((reading) => ({
    time: reading.timestamp.slice(11, 16),
    temperature: reading.temperature_c,
    humidity: reading.humidity_pct,
  }));

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Thermometer size={25} />
          <div>
            <strong>NIMBUS</strong>
            <span>FREIGHT INTELLIGENCE</span>
          </div>
        </div>

        <div className="nav-heading">MONITORING</div>
        <div className="nav-item active">
          <Activity size={18} /> Overview
        </div>
        <div className="nav-item">
          <Truck size={18} /> Fleet Monitoring
        </div>
        <div className="nav-item">
          <Bell size={18} /> Incident History
        </div>

        <div className="sidebar-footer">
          <span className="online-dot" />
          Historical dataset mode
        </div>
      </aside>

      <main className="main-content">
        <header className="page-header">
          <div>
            <div className="eyebrow">OPERATIONS CENTER</div>
            <h1>Cold-Chain Monitoring</h1>
            <p>
              Sensor analytics, temperature excursions,
              and shipment risk visibility.
            </p>
          </div>
          <div className="header-actions">
            <button
              className="refresh-button"
              onClick={loadDashboard}
              disabled={loading}
            >
              <RefreshCw size={16} />
              {loading ? "Loading..." : "Refresh"}
            </button>
            <button className="refresh-button" onClick={onLogout}>
              Logout
            </button>
          </div>
        </header>

        <div className="demo-notice">
          Viewing historical sensor readings from July 20, 2026.
          This is not a live fleet feed.
        </div>
<section className="panel predictive-demo-panel">
  <div className="panel-header">
    <div>
      <h2>Predictive Warning Demonstration</h2>
      <p>
        Run a synthetic temperature-rise scenario using
        the actual backend detection engine.
      </p>
    </div>

    <button
      className="refresh-button"
      onClick={runPredictiveDemo}
      disabled={demoLoading}
    >
      {demoLoading ? "Running..." : "Run Predictive Demo"}
    </button>
  </div>

  {demoError && (
    <div className="error-banner">{demoError}</div>
  )}

  {demoData && (
    <div className="predictive-demo-content">
      <div className="demo-label">
        SYNTHETIC DATA — NOT PART OF THE ORIGINAL DATASET
      </div>

      <div className="demo-metrics">
        <div>
          <strong>Truck</strong>
          <p>{demoData.truck_id}</p>
        </div>

        <div>
          <strong>Current Temperature</strong>
          <p>
            {demoData.readings.at(-1)?.temperature_c}°C
          </p>
        </div>

        <div>
          <strong>Safety Threshold</strong>
          <p>{demoData.threshold_c}°C</p>
        </div>

        <div>
          <strong>Estimated Crossing</strong>
          <p>
            {demoData.incidents[0]?.eta_minutes ?? "—"} minutes
          </p>
        </div>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={demoData.readings.map((reading) => ({
              time: reading.timestamp.slice(11, 16),
              temperature: reading.temperature_c,
            }))}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis domain={[4, 9]} />
            <Tooltip />
            <ReferenceLine
              y={demoData.threshold_c}
              stroke="#ef4444"
              strokeDasharray="6 4"
              label="8°C threshold"
            />
            <Line
              type="linear"
              dataKey="temperature"
              stroke="#f59e0b"
              strokeWidth={3}
              dot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {demoData.incidents.map((incident) => (
        <div className="demo-warning" key={incident.incident_key}>
          <AlertTriangle size={22} />

          <div>
            <strong>
              {incident.type.replaceAll("_", " ")}
            </strong>

            <p>{incident.reason}</p>

            <small>
              Detected at {formatTime(incident.detected_at)}
            </small>
          </div>
        </div>
      ))}
    </div>
  )}
</section>
        {error && <div className="error-banner">{error}</div>}

        <section className="stats-grid">
          <StatCard
            icon={Truck}
            label="Total Trucks"
            value={summary?.total_trucks}
          />
          <StatCard
            icon={AlertTriangle}
            label="Confirmed Violations"
            value={summary?.confirmed_violations}
            tone="danger"
          />
          <StatCard
            icon={Bell}
            label="Predictive Warnings"
            value={summary?.predictive_warnings}
            tone="warning"
          />
          <StatCard
            icon={Database}
            label="Sensor Readings"
            value={summary?.total_readings}
          />
        </section>

        <div className="content-grid">
          <section className="panel">
            <div className="panel-header">
              <div>
                <h2>Fleet Overview</h2>
                <p>Latest recorded sensor measurements</p>
              </div>
              <span className="count-pill">{trucks.length} trucks</span>
            </div>

            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Truck</th>
                    <th>Temperature</th>
                    <th>Threshold</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {trucks.map((truck) => (
                    <tr
                      key={truck.truck_id}
                      className={
                        selectedTruck === truck.truck_id
                          ? "selected-row" : ""
                      }
                      onClick={() => setSelectedTruck(truck.truck_id)}
                    >
                      <td className="truck-id">{truck.truck_id}</td>
                      <td>
                        {truck.latest_temperature_c == null
                          ? "—"
                          : `${truck.latest_temperature_c.toFixed(1)}°C`}
                      </td>
                      <td>{truck.threshold_c}°C</td>
                      <td>
                        <span className={`status ${truck.status}`}>
                          {truck.status === "NORMAL"
                            ? "Within limit"
                            : truck.status === "ABOVE_THRESHOLD"
                              ? "Above threshold"
                              : "No data"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel chart-panel">
            <div className="panel-header">
              <div>
                <h2>Temperature History</h2>
                <p>Recorded readings and safety threshold</p>
              </div>
              <select
                value={selectedTruck}
                onChange={(event) => setSelectedTruck(event.target.value)}
              >
                {trucks.map((truck) => (
                  <option key={truck.truck_id} value={truck.truck_id}>
                    {truck.truck_id}
                  </option>
                ))}
              </select>
            </div>

            <div className="chart-container">
              {chartData.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={chartData}
                    margin={{ top: 15, right: 15, left: -15, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e7edf4" />
                    <XAxis dataKey="time" fontSize={11} />
                    <YAxis domain={["auto", "auto"]} fontSize={11} />
                    <Tooltip
                      formatter={(value) => [`${value}°C`, "Temperature"]}
                    />
                    <ReferenceLine
                      y={history?.threshold_c ?? 8}
                      stroke="#ef4444"
                      strokeDasharray="6 4"
                      label={{ value: "8°C limit", position: "insideTopRight" }}
                    />
                    <Line
                      type="linear"
                      dataKey="temperature"
                      stroke="#2563eb"
                      strokeWidth={3}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                      connectNulls={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-state">No readings available</div>
              )}
            </div>
          </section>
        </div>

        <div className="content-grid bottom-grid">
          <section className="panel">
            <div className="panel-header">
              <div>
                <h2>Incident History</h2>
                <p>Alerts generated by the detection engine</p>
              </div>
              <span className="count-pill">{incidents.length} incidents</span>
            </div>

            <div className="incident-list">
              {incidents.length === 0 && (
                <div className="empty-state">No incidents recorded</div>
              )}

              {incidents.map((incident) => (
                <div className="incident-item" key={incident.id}>
                  <div className="incident-icon">
                    <AlertTriangle size={19} />
                  </div>
                  <div className="incident-body">
                    <div className="incident-title">
                      <strong>{incident.truck_id}</strong>
                      <span className="incident-type">
                        {incident.type.replaceAll("_", " ")}
                      </span>
                    </div>
                    <p>{incident.reason}</p>
                    <small>
                      Detected: {formatTime(incident.detected_at)}
                    </small>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <h2>Data Quality</h2>
                <p>Missing intervals and sensor continuity</p>
              </div>
              <WifiOff size={19} className="muted-icon" />
            </div>

            {gaps.length === 0 ? (
              <div className="empty-state">
                No missing intervals detected
              </div>
            ) : (
              gaps.map((gap, index) => (
                <div className="gap-item" key={index}>
                  <div className="gap-icon">
                    <WifiOff size={20} />
                  </div>
                  <div>
                    <strong>{gap.truck_id} — Missing readings</strong>
                    <p>
                      {gap.gap_minutes}-minute interval between
                      {" "}{formatTime(gap.start_time)} and
                      {" "}{formatTime(gap.end_time)}
                    </p>
                    <small>
                      Gap exceeds the 7-minute continuity tolerance.
                    </small>
                  </div>
                </div>
              ))
            )}
          </section>
        </div>
            
<section className="panel notification-panel">
  <div className="panel-header">
    <div>
      <h2>Notification Delivery History</h2>
      <p>Email and SMS notification audit trail</p>
    </div>
    <span className="count-pill">
      {notifications.length} notifications
    </span>
  </div>

  <div className="table-scroll">
    <table>
      <thead>
        <tr>
          <th>Incident</th>
          <th>Channel</th>
          <th>Recipient</th>
          <th>Status</th>
          <th>Attempts</th>
          <th>Sent At</th>
        </tr>
      </thead>
      <tbody>
        {notifications.map((notification) => (
          <tr key={notification.id}>
            <td>#{notification.incident_id}</td>
            <td>{notification.channel}</td>
            <td>{notification.recipient}</td>
            <td>
              <span
                className={`delivery-status ${notification.status}`}
              >
                {notification.status}
              </span>
            </td>
            <td>{notification.attempt_count}</td>
            <td>{formatTime(notification.sent_at)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
</section>

        <footer>
          Nimbus Freight · Cold-Chain Alerting Engine · Historical replay
        </footer>
      </main>
    </div>
  );
}

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function checkSession() {
      if (!getToken()) {
        if (!cancelled) setChecking(false);
        return;
      }

      try {
        await api.getMe();
        if (!cancelled) setAuthenticated(true);
      } catch {
        clearToken();
        if (!cancelled) setAuthenticated(false);
      } finally {
        if (!cancelled) setChecking(false);
      }
    }

    checkSession();
    return () => { cancelled = true; };
  }, []);

  function logout() {
    clearToken();
    setAuthenticated(false);
  }

  if (checking) {
    return <div className="empty-state">Checking session...</div>;
  }

  if (!authenticated) {
    return <Login onSuccess={() => setAuthenticated(true)} />;
  }

  return <Dashboard onLogout={logout} />;
}

export default App;

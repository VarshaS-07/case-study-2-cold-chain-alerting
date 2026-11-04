
// const API_BASE = "http://127.0.0.1:8000/api";

// async function request(path) {
//   const response = await fetch(`${API_BASE}${path}`);

//   if (!response.ok) {
//     throw new Error(`API request failed: ${response.status}`);
//   }

//   return response.json();
// }

// export const api = {
//   getSummary: () => request("/summary"),
//   getTrucks: () => request("/trucks"),
//   getReadings: (truckId) =>
//     request(`/trucks/${encodeURIComponent(truckId)}/readings`),
//   getIncidents: () => request("/incidents"),
//   getGaps: () => request("/gaps"),
//   getNotifications: () => request("/notifications"),
// };

const API_BASE = "http://127.0.0.1:8000";

export function getToken() {
  return sessionStorage.getItem("nimbus_token");
}

export function saveToken(token) {
  sessionStorage.setItem("nimbus_token", token);
}

export function clearToken() {
  sessionStorage.removeItem("nimbus_token");
}

async function request(path, options = {}) {
  const token = getToken();

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }

  return data;
}

export const api = {
  login: (username, password) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  verifyOTP: (username, otp) =>
    request("/auth/verify-otp", {
      method: "POST",
      body: JSON.stringify({ username, otp }),
    }),

  getMe: () => request("/auth/me"),
getPredictiveDemo: () => request("/api/demo/predictive-warning"),
  getSummary: () => request("/api/summary"),
  getTrucks: () => request("/api/trucks"),
  getReadings: (truckId) =>
    request(`/api/trucks/${encodeURIComponent(truckId)}/readings`),
  getIncidents: () => request("/api/incidents"),
  getGaps: () => request("/api/gaps"),
  getNotifications: () => request("/api/notifications"),
    getIncidents: () => request("/api/incidents"),
  getGaps: () => request("/api/gaps"),
  getNotifications: () => request("/api/notifications"),
  getPredictiveDemo: () => request("/api/demo/predictive-warning"),

};

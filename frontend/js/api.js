/* Design philosophy: keep transport code quiet and explicit so the interface can foreground evidence. Every method returns parsed JSON or throws a readable API error. */
const API_BASE = window.API_BASE || "http://localhost:8000/api";

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = localStorage.getItem("evaluate_token");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(options.body instanceof FormData) && options.body)
    headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new Error(
      data.detail ||
        "Something went wrong while contacting the evaluation service."
    );
  return data;
}

export const api = {
  register: payload =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  login: payload =>
    request("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request("/auth/me"),
  assignments: () => request("/assignments"),
  createAssignment: payload =>
    request("/assignments", { method: "POST", body: JSON.stringify(payload) }),
  updateAssignment: (id, payload) =>
    request(`/assignments/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  submissions: () => request("/submissions"),
  uploadSubmission: (assignmentId, file) => {
    const body = new FormData();
    body.append("assignment_id", assignmentId);
    body.append("file", file);
    return request("/submissions/upload", { method: "POST", body });
  },
  submission: id => request(`/submissions/${id}`),
  matches: id => request(`/submissions/${id}/matches`),
  approve: (id, payload) =>
    request(`/submissions/${id}/approve`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
};

export function saveSession(session) {
  localStorage.setItem("evaluate_token", session.access_token);
  localStorage.setItem("evaluate_user", JSON.stringify(session.user));
}
export function currentUser() {
  try {
    return JSON.parse(localStorage.getItem("evaluate_user") || "null");
  } catch {
    return null;
  }
}
export function clearSession() {
  localStorage.removeItem("evaluate_token");
  localStorage.removeItem("evaluate_user");
}

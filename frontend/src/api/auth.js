import { api } from "./client";

export async function registerRequest(email, password) {
  const { data } = await api.post("/auth/register", { email, password });
  return data;
}

// The backend's login takes form data (that's what Swagger's Authorize button uses).
// "username" holds the email.
export async function loginRequest(email, password) {
  const body = new URLSearchParams({ username: email, password });
  const { data } = await api.post("/auth/login", body);
  return data.access_token;
}

export async function fetchMe() {
  const { data } = await api.get("/auth/me");
  return data;
}
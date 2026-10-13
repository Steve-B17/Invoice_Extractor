import axios from "axios";

const TOKEN_KEY = "invoice_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (token) => localStorage.setItem(TOKEN_KEY, token);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

// Components can register a function that runs when the server says "not logged in"
const unauthorizedHandlers = new Set();
export function onUnauthorized(handler) {
  unauthorizedHandlers.add(handler);
  return () => unauthorizedHandlers.delete(handler);
}

export const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_URL ??
    "https://invoice-extractor-vttj.onrender.com",
});

// Attach the login token to every request
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// An expired or invalid token logs the user out everywhere
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && getToken()) {
      unauthorizedHandlers.forEach((handler) => handler());
    }
    return Promise.reject(error);
  },
);

// Turns an API error into a sentence a person can read
export function errorMessage(error, fallback = "Something went wrong") {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length)
    return detail.map((item) => item.msg).join(". ");
  if (error.request && !error.response)
    return "Cannot reach the server. Is the backend running?";
  return fallback;
}

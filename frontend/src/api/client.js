import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const client = axios.create({ baseURL });

// The JWT lives only in React state (AuthContext), never in storage.
// AuthContext registers a getter here so the interceptor can read the
// current token without every api/*.js file needing its own wiring.
let getToken = () => null;

export function setTokenGetter(fn) {
  getToken = fn;
}

client.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;

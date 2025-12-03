import useAuthStore from "../store/authStore";


// const API_BASE = "https://datacube.uxlivinglab.online";


const API_BASE = "http://127.0.0.1:8000";

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error);
    else prom.resolve(token);
  });
  failedQueue = [];
};

const api = {
  async request(url: string, options: RequestInit = {}) {
    const { accessToken, refreshToken, updateAccessToken, logout } = useAuthStore.getState();

    const fetchWithToken = async (token: string) =>
      fetch(`${API_BASE}${url}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          ...options.headers,
        },
      });

    let res = await fetchWithToken(accessToken!);

    // If 401 → try to refresh token
    if (res.status === 401 && refreshToken && !isRefreshing) {
      isRefreshing = true;

      try {
        const refreshRes = await fetch(`${API_BASE}/core/auth/token/refresh/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh: refreshToken }),
        });

        if (refreshRes.ok) {
          const data = await refreshRes.json();
          updateAccessToken(data.access);
          processQueue(null, data.access);

          // Retry original request with new token
          res = await fetchWithToken(data.access);
        } else {
          throw new Error("Refresh failed");
        }
      } catch (err) {
        processQueue(err, null);
        logout();
        window.location.href = "/login";
        return Promise.reject(new Error("Session expired"));
      } finally {
        isRefreshing = false;
      }
    } else if (res.status === 401) {
      // Refresh failed or no refresh token
      logout();
      window.location.href = "/login";
      return Promise.reject(new Error("Unauthorized"));
    }

    if (!res.ok) {
      let errorMsg = "Request failed";
      try {
        const data = await res.json();
        errorMsg = data.error || data.message || errorMsg;
      } catch {}
      throw new Error(errorMsg);
    }

    return res.ok && res.status !== 204 ? res.json() : null;
  },

  get(url: string) {
    return this.request(url, { method: "GET" });
  },

  post(url: string, data?: any) {
    return this.request(url, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  delete(url: string, data?: any) {
    return this.request(url, {
      method: "DELETE",
      body: data ? JSON.stringify(data) : undefined,
    });
  },
};

export default api;


// // A utility function to check response status and parse body
// const handleResponse = async (res: Response) => {
//   // Check if the HTTP status is in the 200-299 range
//   if (!res.ok) {
//     // Attempt to parse the error message from the body
//     let errorData;
//     try {
//       errorData = await res.json();
//     } catch {
//       // If parsing fails, use the status text
//       throw new Error(`HTTP error! status: ${res.status} ${res.statusText}`);
//     }

//     // Throw an error with a meaningful message from the backend
//     const errorMessage =
//       errorData.error ||
//       errorData.email ||
//       errorData.message ||
//       errorData.detail ||
//       `Request failed with status ${res.status}`;
//     throw new Error(errorMessage);
//   }
//   return res;
// };

// const api = {
//   async get(url: string) {
//     const { token } = useAuthStore.getState();
//     const res = await fetch(`${apiBaseUrl}${url}`, {
//       headers: { Authorization: `Bearer ${token}` },
//     });
//     return handleResponse(res).then((res) => res.json());
//   },

//   async post(url: string, data: unknown) {
//     const { token } = useAuthStore.getState();
//     const res = await fetch(`${apiBaseUrl}${url}`, {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//         Authorization: `Bearer ${token}`,
//       },
//       body: JSON.stringify(data),
//     });
//     // Check status first, then parse JSON on success
//     return handleResponse(res).then((res) => res.json());
//   },

//   async delete(url: string, data?: unknown) {
//     const { token } = useAuthStore.getState();
//     const res = await fetch(`${apiBaseUrl}${url}`, {
//       method: "DELETE",
//       headers: {
//         "Content-Type": "application/json",
//         Authorization: `Bearer ${token}`,
//       },
//       body: JSON.stringify(data),
//     });
//     // Check status first. DELETE may or may not return a body.
//     return handleResponse(res);
//   },
// };

// export default api;

import axios, { AxiosError } from "axios";
import type { AxiosRequestConfig } from "axios";
import useAuthStore from "../store/authStore";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

// State for handling concurrency
let isRefreshing = false;
let failedQueue: any[] = [];

// Helper: Process the queue logic
const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// REQUEST INTERCEPTOR
// Automatically attaches the Access Token to every outgoing request
api.interceptors.request.use(
  (config) => {
    const { accessToken } = useAuthStore.getState();
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// RESPONSE INTERCEPTOR
// Handles global errors, specifically 401 Unauthorized (Token Refresh)
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };
    
    // Prevent infinite loops: check if we already tried to refresh for this request
    if (error.response?.status === 401 && !originalRequest._retry) {
      
      // If a refresh is already happening, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token: string) => {
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${token}`;
              }
              resolve(api(originalRequest));
            },
            reject: (err: any) => reject(err),
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const { refreshToken, updateAccessToken, logout } = useAuthStore.getState();

      if (!refreshToken) {
        logout();
        return Promise.reject(error);
      }

      try {
        // Perform the refresh call (using a fresh axios instance or fetch to avoid interceptor loops)
        const response = await axios.post(`${API_BASE}/core/auth/token/refresh/`, {
          refresh: refreshToken,
        });

        const newAccessToken = response.data.access;

        // 1. Update the store
        updateAccessToken(newAccessToken);

        // 2. Update the header for the failed request
        if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        }
        
        // 3. Process the queue of other requests waiting for this token
        processQueue(null, newAccessToken);

        // 4. Retry the original failed request
        return api(originalRequest);

      } catch (refreshError) {
        // If refresh fails, kill the session
        processQueue(refreshError, null);
        logout();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Return other errors
    return Promise.reject(error);
  }
);

// EXPORTED API WRAPPER
const apiWrapper = {
  get: async (url: string, config?: AxiosRequestConfig) => {
    const response = await api.get(url, config);
    return response.data;
  },
  post: async (url: string, data?: any, config?: AxiosRequestConfig) => {
    const response = await api.post(url, data, config);
    return response.data;
  },
  put: async (url: string, data?: any, config?: AxiosRequestConfig) => {
    const response = await api.put(url, data, config);
    return response.data;
  },
  delete: async (url: string, data?: any, config?: AxiosRequestConfig) => {
    const deleteConfig: AxiosRequestConfig = { ...config };

    if (data) {
        deleteConfig.data = data;
    }
    
    const response = await api.delete(url, deleteConfig);
    return response.data;
  },
  // Exposed raw axios instance for advanced use cases
  raw: api 
};

export default apiWrapper;

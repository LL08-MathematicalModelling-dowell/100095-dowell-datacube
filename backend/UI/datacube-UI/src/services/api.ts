import useAuthStore from "../store/authStore";

// const apiBaseUrl = "http://127.0.0.1:8000";

const apiBaseUrl = "https://datacube.uxlivinglab.online";

// A utility function to check response status and parse body
const handleResponse = async (res: Response) => {
  // Check if the HTTP status is in the 200-299 range
  if (!res.ok) {
    // Attempt to parse the error message from the body
    let errorData;
    try {
      errorData = await res.json();
    } catch {
      // If parsing fails, use the status text
      throw new Error(`HTTP error! status: ${res.status} ${res.statusText}`);
    }

    // Throw an error with a meaningful message from the backend
    const errorMessage =
      errorData.error ||
      errorData.email ||
      errorData.message ||
      errorData.detail ||
      `Request failed with status ${res.status}`;
    throw new Error(errorMessage);
  }
  return res;
};

const api = {
  async get(url: string) {
    const { token } = useAuthStore.getState();
    const res = await fetch(`${apiBaseUrl}${url}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse(res).then((res) => res.json());
  },

  async post(url: string, data: unknown) {
    const { token } = useAuthStore.getState();
    const res = await fetch(`${apiBaseUrl}${url}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    // Check status first, then parse JSON on success
    return handleResponse(res).then((res) => res.json());
  },

  async delete(url: string, data?: unknown) {
    const { token } = useAuthStore.getState();
    const res = await fetch(`${apiBaseUrl}${url}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    // Check status first. DELETE may or may not return a body.
    return handleResponse(res);
  },
};

export default api;

import useAuthStore from "../store/authStore";

const apiBaseUrl = "https://datacube.uxlivinglab.online";

const api = {
  async get(url: string) {
    const { token } = useAuthStore.getState();
    return fetch(`${apiBaseUrl}${url}`, {
      headers: { Authorization: `Bearer ${token}` },
    }).then((res) => res.json());
  },
  async post(url: string, data: unknown) {
    const { token } = useAuthStore.getState();
    return fetch(`${apiBaseUrl}${url}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    }).then((res) => res.json());
  },
  async delete(url: string, data?: unknown) {
    const { token } = useAuthStore.getState();
    return fetch(`${apiBaseUrl}${url}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    }).then((res) => res);
  },
};

export default api;

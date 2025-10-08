import { create } from "zustand";

interface AuthState {
  token: string | null;
  firstName: string | null;
  isAuthenticated: boolean;
  setAuth: (token: string, firstName: string) => void;
  logout: () => void;
}

const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("token") || null,
  firstName: localStorage.getItem("firstName") || null,
  isAuthenticated: !!localStorage.getItem("token"),
  setAuth: (token, firstName) => {
    localStorage.setItem("token", token);
    localStorage.setItem("firstName", firstName);
    set({ token, firstName, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("firstName");
    set({ token: null, firstName: null, isAuthenticated: false });
  },
}));

export default useAuthStore;

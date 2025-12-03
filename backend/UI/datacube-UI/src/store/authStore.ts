// store/authStore.ts
import { create } from "zustand";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  firstName: string | null;
  isAuthenticated: boolean;

  setAuth: (access: string, refresh: string, firstName: string) => void;
  updateAccessToken: (access: string) => void;
  logout: () => void;
}

const useAuthStore = create<AuthState>((set) => ({
  accessToken: localStorage.getItem("accessToken"),
  refreshToken: localStorage.getItem("refreshToken"),
  firstName: localStorage.getItem("firstName"),
  isAuthenticated: !!localStorage.getItem("accessToken"),

  setAuth: (access, refresh, firstName) => {
    localStorage.setItem("accessToken", access);
    localStorage.setItem("refreshToken", refresh);
    localStorage.setItem("firstName", firstName);
    set({ accessToken: access, refreshToken: refresh, firstName, isAuthenticated: true });
  },

  updateAccessToken: (access) => {
    localStorage.setItem("accessToken", access);
    set({ accessToken: access });
  },

  logout: () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("firstName");
    set({ accessToken: null, refreshToken: null, firstName: null, isAuthenticated: false });
  },
}));

export default useAuthStore;



// import { create } from "zustand";

// interface AuthState {
//   token: string | null;
//   firstName: string | null;
//   isAuthenticated: boolean;
//   setAuth: (token: string, firstName: string) => void;
//   logout: () => void;
// }

// const useAuthStore = create<AuthState>((set) => ({
//   token: localStorage.getItem("token") || null,
//   firstName: localStorage.getItem("firstName") || null,
//   isAuthenticated: !!localStorage.getItem("token"),
//   setAuth: (token, firstName) => {
//     localStorage.setItem("token", token);
//     localStorage.setItem("firstName", firstName);
//     set({ token, firstName, isAuthenticated: true });
//   },
//   logout: () => {
//     localStorage.removeItem("token");
//     localStorage.removeItem("firstName");
//     set({ token: null, firstName: null, isAuthenticated: false });
//   },
// }));

// export default useAuthStore;

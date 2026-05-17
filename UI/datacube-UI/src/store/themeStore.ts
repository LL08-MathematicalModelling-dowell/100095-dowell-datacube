import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ThemeMode = "dark" | "light";

type ThemeState = {
  mode: ThemeMode;
  toggle: () => void;
  setMode: (m: ThemeMode) => void;
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: "dark",
      toggle: () =>
        set({ mode: get().mode === "dark" ? "light" : "dark" }),
      setMode: (m) => set({ mode: m }),
    }),
    { name: "datacube-theme" }
  )
);

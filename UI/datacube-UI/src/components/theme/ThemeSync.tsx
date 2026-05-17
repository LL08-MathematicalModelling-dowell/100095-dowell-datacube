import { useEffect } from "react";
import { useThemeStore, type ThemeMode } from "../../store/themeStore";

export function ThemeSync() {
  const mode = useThemeStore((s) => s.mode);

  useEffect(() => {
    const root = document.documentElement;
    const applied: ThemeMode =
      mode === "light" || mode === "dark" ? mode : "dark";
    root.dataset.theme = applied;
    root.style.colorScheme = applied === "dark" ? "dark" : "light";
  }, [mode]);

  return null;
}

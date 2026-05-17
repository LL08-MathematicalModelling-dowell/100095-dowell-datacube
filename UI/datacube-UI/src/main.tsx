import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import App from "./App.tsx";
import "./index.css";
import { Toaster } from "react-hot-toast";
import { useThemeStore } from "./store/themeStore.ts";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 60_000, retry: 1 },
  },
});

function ThemedToaster() {
  const mode = useThemeStore((s) => s.mode);
  const isDark = mode === "dark";
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        duration: 4000,
        style: {
          background: isDark ? "var(--surface-1)" : "var(--surface-1)",
          color: "var(--text-primary)",
          border: "1px solid var(--border-subtle)",
          boxShadow: "var(--shadow-md)",
        },
      }}
    />
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
        <ThemedToaster />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);

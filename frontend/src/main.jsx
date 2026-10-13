import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "sonner";
import App from "./App";
import { ConfirmProvider } from "./components/ConfirmProvider";
import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider, useTheme } from "./context/ThemeContext";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

function AppShell() {
  const { theme } = useTheme();

  return (
    <>
      <App />
      <Toaster
        position="top-center"
        richColors
        closeButton
        theme={theme === "dark" ? "dark" : "light"}
      />
    </>
  );
}

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <ThemeProvider>
            <ConfirmProvider>
              <AppShell />
            </ConfirmProvider>
          </ThemeProvider>
        </AuthProvider>
      </QueryClientProvider>
    </BrowserRouter>
  </StrictMode>,
);

import React from "react";
import { createRoot } from "react-dom/client";
import { AppRouter } from "./app/AppRouter";
import { AuthProvider } from "./auth/AuthContext";
import "./styles/tokens.css";
import "./styles/components.css";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  </React.StrictMode>,
);

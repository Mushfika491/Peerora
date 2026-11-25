import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./auth/AuthContext";
import { ToastProvider } from "./components/Toast";
import { ROUTER_FUTURE } from "./routerFuture";
import "./styles/global.css";
import "./styles/components.css";
import "./styles/layout.css";
import "./styles/pages.css";

const rootElement = document.getElementById("root");

if (rootElement === null) {
  throw new Error("Root element with id 'root' was not found in index.html.");
}

createRoot(rootElement).render(
  <StrictMode>
    <BrowserRouter future={ROUTER_FUTURE}>
      <ToastProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  </StrictMode>
);

import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";
import reportWebVitals from "./reportWebVitals";

// ✅ Fix for TradingView “Script error” during development
// (must come after imports to satisfy ESLint)
window.onerror = function (message, source, lineno, colno, error) {
  if (message === "Script error.") {
    console.warn("⚠️ Ignored harmless TradingView script error");
    return true; // prevent red overlay
  }
  return false;
};

// ✅ Create root and render app
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// ✅ Optional performance metrics
reportWebVitals();

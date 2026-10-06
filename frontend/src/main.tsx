import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import ShareTargetHandler from "./components/ShareTargetHandler";
import "./index.css";

const RootComponent = window.location.pathname === "/share-target" ? ShareTargetHandler : App;

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch((err) => {
      console.error("Service worker registration failed:", err);
    });
  });
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RootComponent />
  </React.StrictMode>
);
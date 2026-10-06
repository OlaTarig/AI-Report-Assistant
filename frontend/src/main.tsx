import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import ShareTargetHandler from "./components/ShareTargetHandler";
import "./index.css";

// Web Launch Queue TypeScript definitions
interface FileSystemHandle {
  readonly kind: "file" | "directory";
  readonly name: string;
}

interface FileSystemFileHandle extends FileSystemHandle {
  readonly kind: "file";
  getFile(): Promise<File>;
}

interface LaunchParams {
  readonly targetURL?: string;
  readonly files: ReadonlyArray<FileSystemFileHandle>;
}

interface LaunchQueue {
  setConsumer(consumer: (launchParams: LaunchParams) => void | Promise<void>): void;
}

declare global {
  interface Window {
    launchQueue?: LaunchQueue;
  }
}

const SHARE_CACHE = "share-target-cache";

// Register launchQueue handler for File Handling API (when tapped in file manager)
const launchQueue = window.launchQueue;

if (launchQueue) {
  launchQueue.setConsumer(async (launchParams: LaunchParams) => {
    if (!launchParams.files.length) return;

    try {
      const files: File[] = [];
      for (const handle of launchParams.files) {
        if (handle.kind === "file") {
          const file = await handle.getFile();
          files.push(file);
        }
      }

      if (files.length > 0) {
        // Save opened files to the same cache used by share_target
        const cache = await caches.open(SHARE_CACHE);
        await cache.put("share-meta", new Response(JSON.stringify({ count: files.length })));

        for (let i = 0; i < files.length; i++) {
          await cache.put(
            `share-file-${i}`,
            new Response(files[i], {
              headers: {
                "Content-Type": files[i].type || "application/octet-stream",
                "X-File-Name": encodeURIComponent(files[i].name),
              },
            })
          );
        }

        // Navigate to /share-target to trigger ShareTargetHandler view if not already there
        if (window.location.pathname !== "/share-target") {
          window.location.href = "/share-target";
        } else {
          // If already on /share-target, reload to re-run ShareTargetHandler
          window.location.reload();
        }
      }
    } catch (err) {
      console.error("Failed to process launchQueue files:", err);
    }
  });
}

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
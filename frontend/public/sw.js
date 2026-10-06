const SHARE_CACHE = "share-target-cache";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method === "POST" && url.pathname === "/share-target") {
    event.respondWith(
      (async () => {
        const cache = await caches.open(SHARE_CACHE);
        const debugLog = {
          receivedAt: new Date().toISOString(),
          contentType: event.request.headers.get("content-type") || "(none)",
        };

        try {
          const formData = await event.request.formData();
          const fieldNames = [...formData.keys()];
          const files = [];

          for (const value of formData.values()) {
            if (value instanceof File) files.push(value);
          }

          debugLog.fieldNames = fieldNames;
          debugLog.fileCount = files.length;
          debugLog.fileNames = files.map((f) => f.name);

          await cache.put(
            "share-meta",
            new Response(JSON.stringify({ count: files.length }), {
              headers: { "Content-Type": "application/json" },
            })
          );

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
        } catch (err) {
          debugLog.error = String(err);
        }

        // Always write the debug log, success or failure, so the page can
        // show exactly what the service worker saw on this specific share.
        await cache.put("share-debug", new Response(JSON.stringify(debugLog)));

        return Response.redirect("/share-target", 303);
      })()
    );
  }
});
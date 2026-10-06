const SHARE_CACHE = "share-target-cache";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method === "POST" && url.pathname === "/share-target") {
    // Intercept POST request and wait until files are stored in Cache API
    event.respondWith(
      (async () => {
        try {
          const formData = await event.request.formData();
          const files = [];

          // Extract ALL files regardless of form parameter name
          for (const value of formData.values()) {
            if (value instanceof File) {
              files.push(value);
            }
          }

          const cache = await caches.open(SHARE_CACHE);

          // Store metadata
          await cache.put(
            "share-meta",
            new Response(JSON.stringify({ count: files.length }), {
              headers: { "Content-Type": "application/json" },
            })
          );

          // Store file payloads
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
          console.error("Service worker failed to store shared files:", err);
        }

        // Redirect AFTER cache writes are complete
        return Response.redirect("/share-target", 303);
      })()
    );
  }
});
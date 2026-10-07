const SHARE_CACHE = "share-target-cache";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  
  if (event.request.method === "POST" && url.pathname === "/share-target") {
    event.respondWith(
      (async () => {
        try {
          const formData = await event.request.clone().formData();
          const files = [];

          // Iterate through all values to catch any file regardless of field name
          for (const value of formData.values()) {
            if (value instanceof File && value.size > 0) {
              files.push(value);
            }
          }

          if (files.length > 0) {
            const cache = await caches.open("share-target-cache");
            await cache.put(
              "share-meta",
              new Response(JSON.stringify({ count: files.length }), {
                headers: { "Content-Type": "application/json" }
              })
            );

            for (let i = 0; i < files.length; i++) {
              await cache.put(
                `share-file-${i}`,
                new Response(files[i], {
                  headers: {
                    "Content-Type": files[i].type || "application/octet-stream",
                    "X-File-Name": encodeURIComponent(files[i].name)
                  }
                })
              );
            }
          }
        } catch (err) {
          console.error("Failed to parse incoming share target formData:", err);
        }

        // Redirect to UI handler page after cache write finishes
        return Response.redirect("/share-target", 303);
      })()
    );
  }
});
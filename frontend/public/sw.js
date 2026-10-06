const SHARE_CACHE = "share-target-cache";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method === "POST" && url.pathname === "/share-target") {
    event.respondWith(handleShareTarget(event));
  }
});

async function handleShareTarget(event) {
  const formData = await event.request.formData();
  const files = formData.getAll("shared_files");
  await storeFilesToCache(files);

  // Redirect to GET /share-target so the app handles UI
  return Response.redirect("/share-target", 303);
}

// Helper to store File objects in Cache API for UI recovery
async function storeFilesToCache(files) {
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
}
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

  // Redirect to a normal page load — the service worker's job (grabbing
  // the files out of the POST) is done; the actual upload happens from
  // regular page JavaScript next, via the existing upload API.
  return Response.redirect("/share-target", 303);
}
const SHARE_CACHE = "share-target-cache";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

function extractBoundary(contentType) {
  const match = contentType.match(/boundary=(?:"([^"]+)"|([^;]+))/);
  return match ? (match[1] || match[2]).trim() : null;
}

function splitOnBoundary(bytes, boundary) {
  const marker = new TextEncoder().encode(`--${boundary}`);
  const parts = [];
  let start = -1;

  for (let i = 0; i <= bytes.length - marker.length; i++) {
    let match = true;
    for (let j = 0; j < marker.length; j++) {
      if (bytes[i + j] !== marker[j]) {
        match = false;
        break;
      }
    }
    if (match) {
      if (start !== -1) parts.push(bytes.slice(start, i));
      start = i + marker.length;
      i += marker.length - 1;
    }
  }
  return parts;
}

function parsePart(part) {
  // Each part looks like: \r\nHeader: val\r\nHeader: val\r\n\r\n<binary body>\r\n
  const headerEnd = findSubarray(part, new TextEncoder().encode("\r\n\r\n"));
  if (headerEnd === -1) return null;

  const headerText = new TextDecoder().decode(part.slice(0, headerEnd));
  const nameMatch = headerText.match(/name="([^"]*)"/);
  const filenameMatch = headerText.match(/filename="([^"]*)"/);
  const typeMatch = headerText.match(/Content-Type:\s*([^\r\n]+)/i);

  if (!filenameMatch || !filenameMatch[1]) return null; // not a file part

  let body = part.slice(headerEnd + 4);
  // Strip the trailing \r\n that precedes the next boundary marker.
  if (body.length >= 2 && body[body.length - 2] === 13 && body[body.length - 1] === 10) {
    body = body.slice(0, body.length - 2);
  }

  return {
    name: nameMatch ? nameMatch[1] : "file",
    filename: filenameMatch[1],
    type: typeMatch ? typeMatch[1].trim() : "application/octet-stream",
    data: body,
  };
}

function findSubarray(haystack, needle) {
  for (let i = 0; i <= haystack.length - needle.length; i++) {
    let match = true;
    for (let j = 0; j < needle.length; j++) {
      if (haystack[i + j] !== needle[j]) {
        match = false;
        break;
      }
    }
    if (match) return i;
  }
  return -1;
}

async function manualParseMultipart(buffer, contentType) {
  const boundary = extractBoundary(contentType);
  if (!boundary) return [];

  const bytes = new Uint8Array(buffer);
  const rawParts = splitOnBoundary(bytes, boundary);
  const files = [];

  for (const raw of rawParts) {
    const parsed = parsePart(raw);
    if (parsed && parsed.data.length > 0) {
      files.push(
        new File([parsed.data], parsed.filename, { type: parsed.type })
      );
    }
  }
  return files;
}

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  if (event.request.method === "POST" && url.pathname === "/share-target") {
    event.respondWith(
      (async () => {
        const cache = await caches.open(SHARE_CACHE);
        const contentType = event.request.headers.get("content-type") || "";
        const debugLog = { receivedAt: new Date().toISOString(), contentType };

        let files = [];

        try {
          // Attempt 1: the browser's built-in parser.
          const formData = await event.request.clone().formData();
          for (const value of formData.values()) {
            if (value instanceof File && value.size > 0) files.push(value);
          }
          debugLog.formDataFileCount = files.length;
        } catch (err) {
          debugLog.formDataError = String(err);
        }

        if (files.length === 0) {
          // Attempt 2: parse the raw multipart body ourselves, in case
          // formData() silently failed on this device/Chrome version.
          try {
            const buffer = await event.request.clone().arrayBuffer();
            debugLog.rawByteLength = buffer.byteLength;
            const manualFiles = await manualParseMultipart(buffer, contentType);
            debugLog.manualParseFileCount = manualFiles.length;
            debugLog.manualParseFileNames = manualFiles.map((f) => f.name);
            if (manualFiles.length > 0) files = manualFiles;
          } catch (err) {
            debugLog.manualParseError = String(err);
          }
        }

        debugLog.finalFileCount = files.length;
        debugLog.finalFileNames = files.map((f) => f.name);

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
        await cache.put("share-debug", new Response(JSON.stringify(debugLog)));

        return Response.redirect("/share-target", 303);
      })()
    );
  }
});
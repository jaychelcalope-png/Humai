const CACHE_NAME = "v1";
const urlsToCache = ["/", "/logo.png", "/manifest.json"];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async cache => {
      for (const url of urlsToCache) {
        try {
          await cache.add(url);
        } catch (err) {
          console.warn("Failed to cache", url, err);
        }
      }
    })
  );
  self.skipWaiting();
});

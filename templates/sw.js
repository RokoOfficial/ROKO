// Service Worker para MOMO PWA
const CACHE_NAME = 'roko-pwa-v1.0.1';
const urlsToCache = [
    '/',
    '/chat',
    '/login',
    '/manifest.json'
];

// Install event
self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Cache opened');
                return cache.addAll(urlsToCache).catch((error) => {
                    console.log('Cache addAll error:', error);
                    return Promise.resolve(); // Continue even if caching fails
                });
            })
            .catch((error) => {
                console.log('Cache open error:', error);
                return Promise.resolve();
            })
    );
    self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch event
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests and API calls
    if (event.request.method !== 'GET' || event.request.url.includes('/api/')) {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // If fetch succeeds, return response and cache it
                if (response && response.status === 200 && response.type === 'basic') {
                    const responseToCache = response.clone();
                    caches.open(CACHE_NAME)
                        .then((cache) => {
                            cache.put(event.request, responseToCache);
                        })
                        .catch(() => {
                            // Silent fail on cache errors
                        });
                }
                return response;
            })
            .catch(() => {
                // If fetch fails, try cache
                return caches.match(event.request).then((response) => {
                    if (response) {
                        return response;
                    }
                    // Fallback for navigation requests
                    if (event.request.mode === 'navigate') {
                        return new Response(`
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <title>MOMO - Offline</title>
                                <meta name="viewport" content="width=device-width, initial-scale=1">
                                <style>
                                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #0f172a; color: #fff; }
                                    .offline { max-width: 400px; margin: 0 auto; }
                                    h1 { color: #6366f1; }
                                    button { background: #6366f1; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
                                </style>
                            </head>
                            <body>
                                <div class="offline">
                                    <h1>MOMO - Offline</h1>
                                    <p>Você está offline. Verifique sua conexão e tente novamente.</p>
                                    <button onclick="location.reload()">Tentar novamente</button>
                                </div>
                            </body>
                            </html>
                        `, {
                            headers: { 'Content-Type': 'text/html' }
                        });
                    }
                    return new Response('Offline', { status: 503 });
                });
            })
    );
});

// Handle messages
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
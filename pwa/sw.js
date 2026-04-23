// 元芳 PWA Service Worker
// 版本: M11
const CACHE_NAME = 'yuanfang-v1';
const STATIC_ASSETS = [
  '/',
  '/dashboard.html',
  '/pwa/manifest.json',
  '/pwa/icons/icon-192.svg',
  '/pwa/icons/icon-512.svg',
];

// API 前缀 — 这些请求永远不走缓存
const API_PREFIX = '/api/';

// 安装：预缓存静态资源
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {
        // 预缓存失败不阻塞安装（某些资源可能在首次部署时不存在）
        console.log('[SW] 部分静态资源预缓存失败，将在 fetch 时回退');
      });
    })
  );
  self.skipWaiting(); // 立即激活，不等待旧 SW 关闭
});

// 激活：清理旧版本缓存
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim(); // 立即控制所有页面
});

// 请求拦截策略：
//   - API 请求 → Network Only（永远获取最新数据）
//   - 静态资源 → Cache First，fallback Network
//   - 离线状态 → 返回缓存（如果有的话）
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // API 请求不走缓存
  if (url.pathname.startsWith(API_PREFIX)) {
    event.respondWith(
      fetch(request).catch(() => {
        // 离线时返回 503 带提示
        return new Response(
          JSON.stringify({ error: '网络不可用，请检查连接' }),
          {
            status: 503,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      })
    );
    return;
  }

  // 非同源请求（如 CDN）不缓存
  if (url.origin !== self.location.origin) {
    event.respondWith(fetch(request));
    return;
  }

  // 静态资源：Cache First
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        // 只缓存成功的 GET 请求
        if (response.ok && request.method === 'GET') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return response;
      }).catch(() => {
        // 离线降级：返回一个简单的离线页面
        if (request.headers.get('accept')?.includes('text/html')) {
          return caches.match('/dashboard.html') || new Response(
            '<!DOCTYPE html><html><body style="background:#0a0e1a;color:#e2e8f0;display:flex;align-items:center;justify-content:center;height:100vh;font-family:system-ui"><div style="text-align:center"><h1>🤖 元芳</h1><p>网络不可用</p><p style="color:#64748b">请检查网络连接后重试</p></div></body></html>',
            { headers: { 'Content-Type': 'text/html' } }
          );
        }
        return new Response('', { status: 408 });
      });
    })
  );
});

// 推送通知处理（预留）
self.addEventListener('push', (event) => {
  const data = event.data?.json() || { title: '元芳通知', body: '你有新消息' };
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/pwa/icons/icon-192.svg',
      badge: '/pwa/icons/icon-192.svg',
      vibrate: [100, 50, 100],
      data: data.url || '/',
      tag: 'yuanfang-notify',
    })
  );
});

// 点击通知打开页面
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes('/') && 'focus' in client) {
          return client.focus();
        }
      }
      return clients.openWindow(event.notification.data || '/');
    })
  );
});

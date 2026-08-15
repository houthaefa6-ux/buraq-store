/* =======================================================================
   بُراق — Service Worker
   الغاية: تمكين تثبيت التطبيق (PWA) + تشغيل الواجهة بلا إنترنت.
   قواعد أمنية مهمة مطبَّقة هنا:
     • لا نخزّن أي طلب إلى Supabase (بيانات، جلسات، توكنات) في الكاش أبدًا.
     • لا نخزّن إلا طلبات GET من نفس النطاق.
     • صفحة index.html تُجلب من الشبكة أولًا حتى تصل التحديثات الأمنية فورًا.
     • عند رجوع تسجيل الدخول من Google (رابط فيه code= أو access_token)
       نمرّر الطلب للشبكة مباشرة بلا أي تدخّل.
   بعد أي تعديل على الموقع: ارفع الرقم في CACHE_VERSION لتحديث الكاش.
   ======================================================================= */

const CACHE_VERSION = 'buraq-v1';
const CORE_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-192.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION)
      .then((cache) => cache.addAll(CORE_ASSETS).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', (event) => {
  if (event.data === 'skipWaiting') self.skipWaiting();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;

  // 1) لا نتدخّل إلا في GET
  if (req.method !== 'GET') return;

  let url;
  try { url = new URL(req.url); } catch (e) { return; }

  // 2) لا نتدخّل في أي طلب خارج نطاق الموقع (Supabase، خطوط Google، صور خارجية)
  if (url.origin !== self.location.origin) return;

  // 3) لا نلمس روابط رجوع تسجيل الدخول
  if (url.search.includes('code=') || url.hash.includes('access_token')) return;

  const isDocument = req.mode === 'navigate' ||
    (req.headers.get('accept') || '').includes('text/html');

  // 4) الصفحة نفسها: الشبكة أولًا، والكاش احتياط عند انقطاع الإنترنت
  if (isDocument) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE_VERSION).then((c) => c.put('./index.html', copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match('./index.html').then((r) => r || offlinePage()))
    );
    return;
  }

  // 5) بقية ملفات الموقع (أيقونات وغيرها): الكاش أولًا لسرعة الإقلاع
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req).then((res) => {
        if (res && res.status === 200 && res.type === 'basic') {
          const copy = res.clone();
          caches.open(CACHE_VERSION).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      }).catch(() => cached);
    })
  );
});

function offlinePage() {
  return new Response(
    '<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8">' +
    '<meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<title>بُراق — لا يوجد اتصال</title></head>' +
    '<body style="margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;' +
    'background:#F8F5EF;color:#1E2F46;font-family:system-ui,sans-serif;text-align:center;padding:24px;">' +
    '<div><div style="font-size:44px;margin-bottom:12px;">📡</div>' +
    '<h2 style="margin:0 0 8px;color:#173A63;">ما في اتصال بالإنترنت</h2>' +
    '<p style="color:#6B7280;font-size:14px;">تأكد من الشبكة وأعد المحاولة.</p></div></body></html>',
    { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
  );
}

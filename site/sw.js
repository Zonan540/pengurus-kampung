// Service worker Pengurus Kampung (Versi 1.4). Tukar CACHE setiap kali versi baharu dikeluarkan.
const CACHE='pk-2-0-b5';
const CORE=['./','index.html','manifest.webmanifest','vendor/lz-string.min.js','vendor/fflate.min.js','icons/icon-192.png','icons/icon-512.png','icons/icon-maskable-512.png','icons/logo-pk.webp','icons/logo-tbpm.webp'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;const u=new URL(r.url);
  if(u.pathname.endsWith('/beta.json'))return;
  const scope=new URL(self.registration.scope).pathname;
  const isGame=u.pathname===scope||u.pathname.endsWith('/index.html');
  if(isGame&&(r.mode==='navigate'||u.pathname.endsWith('/index.html'))){e.respondWith(fetch(r).then(res=>{if(res&&res.ok){const cp=res.clone();caches.open(CACHE).then(c=>c.put('index.html',cp))}return res}).catch(()=>caches.match('index.html')));return}
  if(r.mode==='navigate'){e.respondWith(fetch(r).then(res=>{if(res&&res.ok){const cp=res.clone();caches.open(CACHE).then(c=>c.put(r,cp))}return res}).catch(()=>caches.match(r).then(hit=>hit||caches.match('index.html'))));return}
  const ok=u.origin===location.origin||/fonts\.(googleapis|gstatic)\.com$/.test(u.hostname);if(!ok)return;
  e.respondWith(caches.match(r).then(hit=>{const net=fetch(r).then(res=>{if(res&&(res.ok||res.type==='opaque')){const cp=res.clone();caches.open(CACHE).then(c=>c.put(r,cp))}return res}).catch(()=>hit);return hit||net}))});

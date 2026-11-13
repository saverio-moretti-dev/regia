"use strict";
/* Regia — service worker minimo. Le /api/ non passano mai dalla cache (dati sempre vivi).
   La pagina e i file statici: prima la rete; se il server è spento si mostra l'ultima copia,
   e la pagina stessa dice «server non raggiungibile». */
const CACHE = "regia-v15"; // v15: terminale in ogni riga, lampo % (12/11); v14: allegati (12/11); v13: pulsante Risparmio token (12/11); v12: avviso limiti, correzioni Da decidere (12/11); v11: ritmo %/ora in testata (12/11); v10: Da decidere / Fatto (12/11); v9: riquadro Promemoria (12/11); v7: riga Fissati (12/11); v6: avviso riavvii (12/11); v5: bottoni copia, selezione tenuta (12/11); v4: chat allineata, Terminale (11/11); v3: riga ascolto + Terminale (11/11); v2: icone nuove
const GUSCIO = ["/", "/style.css", "/app.js", "/token.js", "/manifest.webmanifest", "/icone/regia-192.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(GUSCIO)).catch(() => {}).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((k) => Promise.all(k.filter((n) => n !== CACHE).map((n) => caches.delete(n))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== self.location.origin || u.pathname.startsWith("/api/")) return;
  e.respondWith(
    fetch(e.request).then((r) => {
      if (r.ok) { const copia = r.clone(); caches.open(CACHE).then((c) => c.put(u.pathname === "/index.html" ? "/" : e.request, copia)); }
      return r;
    }).catch(() => caches.match(u.pathname === "/index.html" ? "/" : e.request, { ignoreSearch: true }))
  );
});

/* clic su una notifica: porta in primo piano la finestra della Regia */
self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({ type: "window" }).then((w) => (w[0] ? w[0].focus() : self.clients.openWindow("/"))));
});

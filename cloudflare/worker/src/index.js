/* Cloudflare Worker: static public bundle + D1-backed public gallery.
 *
 * Library-only deployment: no Python runtime and no LLM calls. A share copies
 * the already-built PUBLIC_BUILD files from the library/ prefix to shared/<id>/
 * and records an expiring row in D1.
 */

const SUBJECT = "CSC662";
const DEFAULT_TTL_DAYS = 7;
const DEFAULT_MAX_ENTRIES = 100;
const ID_RE = /^[a-f0-9]{32}$/;

const PAGE_MAP = {
  "/": "index.html",
  "/index.html": "index.html",
  "/csc662": "csc662/index.html",
  "/csc662/": "csc662/index.html",
  "/csc662/library": "csc662/library/index.html",
  "/csc662/library/": "csc662/library/index.html",
  "/csc662/generate": "csc662/generate/index.html",
  "/csc662/generate/": "csc662/generate/index.html",
  "/gallery": "gallery/index.html",
  "/gallery/": "gallery/index.html",
  "/paused": "paused/index.html",
  "/paused/": "paused/index.html",
};

const CONTENT_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".pdf": "application/pdf",
  ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ".txt": "text/plain; charset=utf-8",
};

export function contentType(key) {
  const dot = key.lastIndexOf(".");
  return CONTENT_TYPES[key.slice(dot).toLowerCase()] || "application/octet-stream";
}

export function pageKey(pathname) {
  let decoded;
  try {
    decoded = decodeURIComponent(pathname);
  } catch {
    return null;
  }
  if (decoded.includes("..") || decoded.includes("\0")) return null;
  if (PAGE_MAP[decoded]) return PAGE_MAP[decoded];
  for (const prefix of ["/assets/", "/library/", "/subjects/", "/static/"]) {
    if (decoded.startsWith(prefix)) return decoded.slice(1);
  }
  return null;
}

export function disposition(name) {
  const ascii = name
    .normalize("NFKD")
    .replace(/[^\x20-\x7e]/g, "")
    .replace(/["\\]/g, "_") || "download";
  return `attachment; filename="${ascii}"; filename*=UTF-8''${encodeURIComponent(name)}`;
}

export function normaliseShare(body) {
  if (!body || typeof body !== "object") throw new Error("invalid request");
  const allowed = new Set(["subject", "mode", "seed"]);
  for (const key of Object.keys(body)) {
    if (!allowed.has(key)) throw new Error("unexpected field");
  }
  if (body.subject !== SUBJECT) throw new Error("unknown subject");
  if (body.mode !== "realistic") {
    throw new Error("only realistic library papers can be shared");
  }
  const seed = Number(body.seed);
  if (!Number.isInteger(seed) || seed < 1 || seed > 20) {
    throw new Error("seed must be an integer from 1 to 20");
  }
  return { subject: SUBJECT, mode: "realistic", seed };
}

function maxEntries(env) {
  const value = Number(env.MAX_GALLERY_ENTRIES);
  return Number.isFinite(value) && value > 0 ? value : DEFAULT_MAX_ENTRIES;
}

function ttlDays(env) {
  const value = Number(env.GALLERY_TTL_DAYS);
  return Number.isFinite(value) && value >= 1 ? value : DEFAULT_TTL_DAYS;
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}

function notFound() {
  return new Response("Not found", {
    status: 404,
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
}

function cacheControl(key) {
  if (key.endsWith(".html")) return "public, max-age=300";
  if (key.startsWith("assets/")) return "public, max-age=31536000, immutable";
  if (key.startsWith("library/")) return "public, max-age=86400";
  return "public, max-age=300";
}

function staticHeaders(key, size, etag) {
  const headers = new Headers({
    "Content-Type": contentType(key),
    "Cache-Control": cacheControl(key),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
  });
  if (size != null) headers.set("Content-Length", String(size));
  if (etag) headers.set("ETag", etag);
  if (/\.(pdf|docx)$/i.test(key)) {
    headers.set("Content-Disposition",
      disposition(key.split("/").pop() || "download"));
  }
  return headers;
}

async function serveStatic(request, env, url) {
  const key = pageKey(url.pathname);
  if (!key) return notFound();
  if (request.method === "HEAD") {
    const head = await env.BUCKET.head(key);
    if (!head) return notFound();
    return new Response(null, {
      headers: staticHeaders(key, head.size, head.httpEtag),
    });
  }
  const object = await env.BUCKET.get(key);
  if (!object) return notFound();
  if (request.headers.get("If-None-Match") === object.httpEtag) {
    return new Response(null, {
      status: 304,
      headers: { ETag: object.httpEtag },
    });
  }
  return new Response(object.body, {
    headers: staticHeaders(key, object.size, object.httpEtag),
  });
}

async function listGallery(env) {
  const now = new Date().toISOString();
  const rows = await env.DB.prepare(
    `SELECT id, subject, seed, mode, computed_marks, created_at, expires_at
       FROM gallery
      WHERE expires_at > ?
      ORDER BY created_at DESC
      LIMIT 100`,
  ).bind(now).all();
  const items = (rows.results || []).map((row) => ({
    ...row,
    expires_in_days: Math.max(0, Math.ceil(
      (Date.parse(row.expires_at) - Date.now()) / 86400000)),
    files: {
      paper_pdf: `/api/gallery/${row.id}/paper.pdf`,
      paper_docx: `/api/gallery/${row.id}/paper.docx`,
      scheme_pdf: `/api/gallery/${row.id}/scheme.pdf`,
      scheme_docx: `/api/gallery/${row.id}/scheme.docx`,
    },
  }));
  return json({ items });
}

async function sharePaper(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid JSON" }, 400);
  }
  let share;
  try {
    share = normaliseShare(body);
  } catch (error) {
    return json({ error: error.message }, 400);
  }

  const now = new Date().toISOString();
  const existing = await env.DB.prepare(
    `SELECT id, expires_at FROM gallery
      WHERE subject = ? AND mode = ? AND seed = ? AND expires_at > ?
      ORDER BY created_at DESC LIMIT 1`,
  ).bind(share.subject, share.mode, share.seed, now).first();
  if (existing) {
    return json({
      id: existing.id, existing: true, expires_at: existing.expires_at,
      gallery_url: "/gallery",
    });
  }

  const count = await env.DB.prepare(
    "SELECT COUNT(*) AS n FROM gallery WHERE expires_at > ?",
  ).bind(now).first();
  if ((count && count.n ? Number(count.n) : 0) >= maxEntries(env)) {
    return json({ error: "Gallery is full; try again after entries expire." },
      429);
  }

  const manifestObject = await env.BUCKET.get(
    `library/${SUBJECT}/manifest.json`);
  if (!manifestObject) return json({ error: "Library manifest missing" }, 500);
  const manifest = await manifestObject.json();
  const entry = (manifest.papers || []).find(
    (paper) => paper.seed === share.seed && paper.mode === share.mode);
  if (!entry) return json({ error: "Library paper not found" }, 404);

  const id = crypto.randomUUID().replace(/-/g, "");
  const expires = new Date(
    Date.now() + ttlDays(env) * 86400000).toISOString();
  const targets = {
    paper_docx: `shared/${id}/paper.docx`,
    paper_pdf: `shared/${id}/paper.pdf`,
    scheme_docx: `shared/${id}/scheme.docx`,
    scheme_pdf: `shared/${id}/scheme.pdf`,
  };
  const names = {};
  const copied = [];
  try {
    for (const kind of Object.keys(targets)) {
      const sourceKey = entry.files && entry.files[kind];
      if (!sourceKey) throw new Error(`missing ${kind}`);
      const object = await env.BUCKET.get(sourceKey);
      if (!object) throw new Error(`missing object ${sourceKey}`);
      await env.BUCKET.put(targets[kind], object.body, {
        httpMetadata: { contentType: contentType(sourceKey) },
      });
      copied.push(targets[kind]);
      names[kind] = sourceKey.split("/").pop();
    }
    await env.DB.prepare(
      `INSERT INTO gallery
        (id, subject, seed, mode, computed_marks, created_at, expires_at,
         paper_pdf_key, paper_docx_key, scheme_pdf_key, scheme_docx_key,
         paper_pdf_name, paper_docx_name, scheme_pdf_name, scheme_docx_name)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    ).bind(
      id, share.subject, share.seed, share.mode,
      entry.computed_marks ?? null, now, expires,
      targets.paper_pdf, targets.paper_docx,
      targets.scheme_pdf, targets.scheme_docx,
      names.paper_pdf, names.paper_docx,
      names.scheme_pdf, names.scheme_docx,
    ).run();
  } catch (error) {
    if (copied.length) await env.BUCKET.delete(copied);
    return json({ error: "Could not share paper" }, 500);
  }
  return json({
    id, existing: false, expires_at: expires, gallery_url: "/gallery",
  });
}

async function serveShared(env, id, kind, ext) {
  if (!ID_RE.test(id)) return notFound();
  const row = await env.DB.prepare(
    `SELECT * FROM gallery
      WHERE id = ? AND expires_at > ? LIMIT 1`,
  ).bind(id, new Date().toISOString()).first();
  if (!row) return notFound();
  const key = row[`${kind}_${ext}_key`];
  const name = row[`${kind}_${ext}_name`];
  if (!key) return notFound();
  const object = await env.BUCKET.get(key);
  if (!object) return notFound();
  return new Response(object.body, {
    headers: {
      "Content-Type": contentType(key),
      "Content-Disposition": disposition(name || `${kind}.${ext}`),
      "Cache-Control": "private, max-age=300",
      "X-Content-Type-Options": "nosniff",
    },
  });
}

async function purgeExpired(env) {
  const now = new Date().toISOString();
  for (let batch = 0; batch < 10; batch += 1) {
    const rows = await env.DB.prepare(
      `SELECT * FROM gallery WHERE expires_at <= ? LIMIT 50`,
    ).bind(now).all();
    const expired = rows.results || [];
    if (!expired.length) return;
    for (const row of expired) {
      const keys = [
        row.paper_pdf_key, row.paper_docx_key,
        row.scheme_pdf_key, row.scheme_docx_key,
      ].filter(Boolean);
      if (keys.length) await env.BUCKET.delete(keys);
    }
    await env.DB.batch(expired.map(
      (row) => env.DB.prepare("DELETE FROM gallery WHERE id = ?").bind(row.id),
    ));
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const method = request.method;

    if (url.pathname === "/api/gallery" && method === "GET") {
      return listGallery(env);
    }
    if (url.pathname === "/api/gallery/share" && method === "POST") {
      return sharePaper(request, env);
    }
    const shared = url.pathname.match(
      /^\/api\/gallery\/([a-f0-9]{32})\/(paper|scheme)\.(pdf|docx)$/,
    );
    if (shared && (method === "GET" || method === "HEAD")) {
      return serveShared(env, shared[1], shared[2], shared[3]);
    }
    if (url.pathname.startsWith("/api/")) return notFound();
    if (method !== "GET" && method !== "HEAD") {
      return new Response("Method not allowed", {
        status: 405,
        headers: { Allow: "GET, HEAD" },
      });
    }
    return serveStatic(request, env, url);
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(purgeExpired(env));
  },
};

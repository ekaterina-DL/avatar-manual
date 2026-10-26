// Вход на сайт мануала по условным логинам (Assessor1, Assessor2...) и паролям.
// Работает как Cloudflare Pages Function перед КАЖДЫМ запросом: страницы, картинки, видео,
// поиск. Без действующего входа не отдаётся ничего, кроме страницы входа.
//
// Хранилище — база D1 (привязка env.DB, схема в ../schema.sql). Подпись сеанса — секрет
// env.SESSION_SECRET. Почт и имён нет: таблица «логин = человек» хранится только локально.

export const SESSION_DAYS = 14;
export const MAX_FAILS = 5;
export const LOCK_MINUTES = 15;
export const PBKDF2_ITERATIONS = 10000; // пароли случайные и длинные, перебор отсекает блокировка
export const EVENTS_KEEP_DAYS = 180;
export const COOKIE = "__Host-s";

const LOGIN_PATH = "/__login";
const LOGOUT_PATH = "/__logout";
const LOGIN_RE = /^[A-Za-z0-9_-]{1,40}$/;
const enc = new TextEncoder();

// --- base64url -------------------------------------------------------------------------------

function b64u(bytes) {
  let s = "";
  for (const b of new Uint8Array(bytes)) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function unb64u(str) {
  const s = str.replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(s + "===".slice((s.length + 3) % 4));
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
}

// --- пароли ------------------------------------------------------------------------------------

async function pbkdf2(password, salt, iterations) {
  const key = await crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt, iterations }, key, 256);
  return new Uint8Array(bits);
}

export async function hashPassword(password, iterations = PBKDF2_ITERATIONS) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const hash = await pbkdf2(password, salt, iterations);
  return `pbkdf2$${iterations}$${b64u(salt)}$${b64u(hash)}`;
}

function sameBytes(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

export async function verifyPassword(password, stored) {
  const parts = String(stored || "").split("$");
  if (parts.length !== 4 || parts[0] !== "pbkdf2") return false;
  const iterations = Number(parts[1]);
  if (!Number.isInteger(iterations) || iterations < 1000 || iterations > 100000) return false;
  const hash = await pbkdf2(password, unb64u(parts[2]), iterations);
  return sameBytes(hash, unb64u(parts[3]));
}

// Хэш-пустышка: для несуществующего логина считаем столько же, сколько для настоящего,
// чтобы по времени ответа нельзя было угадать, какие логины есть.
const DUMMY_HASH = "pbkdf2$10000$AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";

// --- сеанс -------------------------------------------------------------------------------------

async function hmacKey(secret) {
  if (!secret || secret.length < 32) throw new Error("SESSION_SECRET не задан или слишком короткий");
  return crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]);
}

export async function signSession(data, secret) {
  const body = b64u(enc.encode(JSON.stringify(data)));
  const sig = await crypto.subtle.sign("HMAC", await hmacKey(secret), enc.encode(body));
  return `${body}.${b64u(sig)}`;
}

export async function readSession(token, secret, now) {
  if (!token || typeof token !== "string") return null;
  const dot = token.indexOf(".");
  if (dot < 1) return null;
  const body = token.slice(0, dot);
  let ok = false;
  try {
    ok = await crypto.subtle.verify("HMAC", await hmacKey(secret), unb64u(token.slice(dot + 1)), enc.encode(body));
  } catch {
    return null;
  }
  if (!ok) return null;
  let data;
  try {
    data = JSON.parse(new TextDecoder().decode(unb64u(body)));
  } catch {
    return null;
  }
  if (!data || typeof data.l !== "string" || typeof data.e !== "number" || data.e <= now) return null;
  return data;
}

function getCookie(request, name) {
  const header = request.headers.get("Cookie") || "";
  for (const part of header.split(";")) {
    const i = part.indexOf("=");
    if (i > 0 && part.slice(0, i).trim() === name) return part.slice(i + 1).trim();
  }
  return null;
}

function sessionCookie(value, maxAgeSeconds) {
  return `${COOKIE}=${value}; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=${maxAgeSeconds}`;
}

// --- роли --------------------------------------------------------------------------------------

export function parseGroups(groups) {
  return String(groups || "").split(",").map((g) => g.trim()).filter(Boolean);
}

// Мануал 3 этапа — только группе stage3 (и admin). Остальное — любому, кто вошёл.
export function canAccess(groups, path) {
  const g = parseGroups(groups);
  if (g.includes("admin")) return true;
  if (path.startsWith("/manual-3-etap/")) return g.includes("stage3");
  return true;
}

// --- страницы ----------------------------------------------------------------------------------

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

const PAGE_HEADERS = {
  "Content-Type": "text/html; charset=utf-8",
  "Cache-Control": "no-store",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "no-referrer",
};

function page(title, inner, status = 200, extraHeaders = {}) {
  const html = `<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>${esc(title)}</title><style>
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:#f5f5f4;color:#1c1917}
.box{background:#fff;padding:32px 36px;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,.12);width:100%;max-width:340px}
h1{font-size:20px;margin:0 0 20px}label{display:block;font-size:14px;margin:14px 0 6px}
input{width:100%;box-sizing:border-box;padding:10px 12px;font-size:16px;border:1px solid #d6d3d1;border-radius:8px}
button{margin-top:22px;width:100%;padding:11px;font-size:16px;border:0;border-radius:8px;background:#b45309;color:#fff;cursor:pointer}
.err{background:#fef2f2;color:#991b1b;padding:10px 12px;border-radius:8px;font-size:14px;margin-bottom:6px}
p{font-size:14px;line-height:1.5}a{color:#b45309}
</style></head><body><div class="box">${inner}</div></body></html>`;
  return new Response(html, { status, headers: { ...PAGE_HEADERS, ...extraHeaders } });
}

function loginPage(next, error, status = 200) {
  return page(
    "Вход",
    `<h1>Вход в мануал</h1>${error ? `<div class="err">${esc(error)}</div>` : ""}
<form method="post" action="${LOGIN_PATH}">
<input type="hidden" name="next" value="${esc(next)}">
<label for="l">Логин</label><input id="l" name="login" autocomplete="username" required autofocus>
<label for="p">Пароль</label><input id="p" name="password" type="password" autocomplete="current-password" required>
<button type="submit">Войти</button></form>
<p>Нет логина или забыли пароль — напишите руководителю группы.</p>`,
    status,
  );
}

function redirect(location, extraHeaders = {}) {
  return new Response(null, { status: 303, headers: { Location: location, "Cache-Control": "no-store", ...extraHeaders } });
}

// Куда вернуть после входа: только путь этого же сайта.
export function safeNext(next) {
  if (typeof next !== "string" || !next.startsWith("/") || next.startsWith("//") || next.startsWith("/\\")) return "/";
  if (next.startsWith(LOGIN_PATH) || next.startsWith(LOGOUT_PATH)) return "/";
  return next.slice(0, 500);
}

// --- журнал ------------------------------------------------------------------------------------

async function logEvent(env, now, login, kind, path = null) {
  await env.DB.prepare("INSERT INTO events (ts, login, kind, path) VALUES (?, ?, ?, ?)")
    .bind(now, String(login).slice(0, 40), kind, path ? String(path).slice(0, 300) : null)
    .run();
}

function isPageView(path) {
  return path.endsWith("/") || path.endsWith(".html");
}

// --- вход --------------------------------------------------------------------------------------

async function handleLogin(request, env, now) {
  if (request.method !== "POST") {
    const next = safeNext(new URL(request.url).searchParams.get("next"));
    return loginPage(next);
  }
  let form;
  try {
    form = await request.formData();
  } catch {
    return loginPage("/", "Неверный логин или пароль", 400);
  }
  const login = String(form.get("login") || "").trim();
  const password = String(form.get("password") || "");
  const next = safeNext(String(form.get("next") || "/"));
  const generic = "Неверный логин или пароль";

  if (!LOGIN_RE.test(login) || password.length === 0 || password.length > 200) {
    await verifyPassword(password || "x", DUMMY_HASH);
    return loginPage(next, generic, 401);
  }

  const user = await env.DB.prepare("SELECT login, pw, groups, active, sv, fails, locked_until FROM users WHERE login = ?")
    .bind(login).first();

  if (!user) {
    await verifyPassword(password, DUMMY_HASH);
    await logEvent(env, now, login, "login_fail");
    return loginPage(next, generic, 401);
  }

  if (user.locked_until > now) {
    const minutes = Math.ceil((user.locked_until - now) / 60000);
    await logEvent(env, now, user.login, "locked");
    return loginPage(next, `Слишком много неверных попыток. Попробуйте через ${minutes} мин.`, 429);
  }

  const ok = await verifyPassword(password, user.pw);
  if (!ok || !user.active) {
    const fails = (user.fails || 0) + 1;
    if (fails >= MAX_FAILS) {
      await env.DB.prepare("UPDATE users SET fails = 0, locked_until = ? WHERE login = ?")
        .bind(now + LOCK_MINUTES * 60000, user.login).run();
    } else {
      await env.DB.prepare("UPDATE users SET fails = ? WHERE login = ?").bind(fails, user.login).run();
    }
    await logEvent(env, now, user.login, "login_fail");
    return loginPage(next, generic, 401);
  }

  await env.DB.prepare("UPDATE users SET fails = 0, locked_until = 0 WHERE login = ?").bind(user.login).run();
  await logEvent(env, now, user.login, "login_ok");
  await env.DB.prepare("DELETE FROM events WHERE ts < ?").bind(now - EVENTS_KEEP_DAYS * 86400000).run();

  const token = await signSession({ l: user.login, v: user.sv, e: now + SESSION_DAYS * 86400000 }, env.SESSION_SECRET);
  return redirect(next, { "Set-Cookie": sessionCookie(token, SESSION_DAYS * 86400) });
}

// --- частичная отдача видео --------------------------------------------------------------------
// Хранилище Pages за функцией отдаёт файл целиком (200) даже на запрос «Range: bytes=…»,
// а без ответа 206 браузер не умеет перематывать видео, пока оно не скачано. Поэтому
// нужный кусок вырезаем сами, потоком, не держа файл в памяти.

function isMedia(path) {
  return /\.(mp4|webm|mov|m4a|mp3)$/i.test(path);
}

export function parseRange(header, size) {
  const m = /^bytes=(\d*)-(\d*)$/.exec(String(header || "").trim());
  if (!m || (m[1] === "" && m[2] === "")) return null;
  let start, end;
  if (m[1] === "") {
    const suffix = Number(m[2]);
    if (suffix === 0) return null;
    start = Math.max(0, size - suffix);
    end = size - 1;
  } else {
    start = Number(m[1]);
    end = m[2] === "" ? size - 1 : Math.min(Number(m[2]), size - 1);
  }
  if (start > end || start >= size) return "unsatisfiable";
  return { start, end };
}

function sliceStream(body, start, end) {
  let pos = 0;
  return body.pipeThrough(new TransformStream({
    transform(chunk, controller) {
      const from = Math.max(start - pos, 0);
      const to = Math.min(end + 1 - pos, chunk.byteLength);
      if (from < to) controller.enqueue(chunk.subarray(from, to));
      pos += chunk.byteLength;
      if (pos > end) controller.terminate();
    },
  }));
}

async function rangeResponse(request, res) {
  const header = request.headers.get("Range");
  if (!header || res.status !== 200 || !res.body) return null;
  let size = Number(res.headers.get("Content-Length") || NaN);
  // Ответ хранилища внутри функции может прийти без длины — тогда читаем файл в память
  // (видео на сайте не больше 25 МБ, это ограничение Pages).
  let buffered = null;
  if (!Number.isFinite(size) || size <= 0) {
    buffered = new Uint8Array(await res.arrayBuffer());
    size = buffered.byteLength;
    if (size === 0) return null;
  }
  const range = parseRange(header, size);
  if (!range) return buffered ? new Response(buffered, { status: 200, headers: res.headers }) : null;
  const headers = new Headers(res.headers);
  if (buffered) {
    headers.set("Cache-Control", "private, max-age=0, must-revalidate");
    headers.set("Accept-Ranges", "bytes");
    if (range === "unsatisfiable") {
      headers.set("Content-Range", `bytes */${size}`);
      headers.delete("Content-Length");
      return new Response(null, { status: 416, headers });
    }
    headers.set("Content-Range", `bytes ${range.start}-${range.end}/${size}`);
    headers.set("Content-Length", String(range.end - range.start + 1));
    const part = request.method === "HEAD" ? null : buffered.subarray(range.start, range.end + 1);
    return new Response(part, { status: 206, headers });
  }
  headers.set("Cache-Control", "private, max-age=0, must-revalidate");
  headers.set("Accept-Ranges", "bytes");
  if (range === "unsatisfiable") {
    res.body.cancel();
    headers.set("Content-Range", `bytes */${size}`);
    headers.delete("Content-Length");
    return new Response(null, { status: 416, headers });
  }
  headers.set("Content-Range", `bytes ${range.start}-${range.end}/${size}`);
  headers.set("Content-Length", String(range.end - range.start + 1));
  let body = request.method === "HEAD" ? null : sliceStream(res.body, range.start, range.end);
  // В Cloudflare длина у потокового ответа сохраняется только через FixedLengthStream.
  if (body && typeof FixedLengthStream === "function") {
    body = body.pipeThrough(new FixedLengthStream(range.end - range.start + 1));
  }
  if (!body) res.body.cancel();
  return new Response(body, { status: 206, headers });
}

// --- главный обработчик ------------------------------------------------------------------------

export async function handle(request, env, next, waitUntil, now = Date.now()) {
  const url = new URL(request.url);
  const path = url.pathname;

  if (path === LOGIN_PATH) return handleLogin(request, env, now);

  const session = await readSession(getCookie(request, COOKIE), env.SESSION_SECRET, now);
  const user = session
    ? await env.DB.prepare("SELECT login, groups, active, sv FROM users WHERE login = ?").bind(session.l).first()
    : null;
  const valid = user && user.active && user.sv === session.v;

  if (path === LOGOUT_PATH) {
    if (valid) await logEvent(env, now, user.login, "logout");
    return redirect(LOGIN_PATH, { "Set-Cookie": sessionCookie("", 0) });
  }

  if (!valid) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Требуется вход", { status: 401, headers: { "Cache-Control": "no-store" } });
    }
    return redirect(`${LOGIN_PATH}?next=${encodeURIComponent(path + url.search)}`);
  }

  if (!canAccess(user.groups, path)) {
    return page("Нет доступа", `<h1>Нет доступа</h1><p>Этот раздел вам не открыт. Если он нужен, напишите руководителю группы.</p><p><a href="/">На главную</a></p>`, 403);
  }

  if (isPageView(path) && request.method === "GET") {
    waitUntil(logEvent(env, now, user.login, "view", path).catch(() => {}));
  }

  const res = await next();
  const ranged = await rangeResponse(request, res);
  if (ranged) return ranged;
  const out = new Response(res.body, res);
  if (isMedia(path)) out.headers.set("Accept-Ranges", "bytes");
  // private: ответ только для этого браузера, промежуточным кэшам хранить нельзя.
  out.headers.set("Cache-Control", "private, max-age=0, must-revalidate");
  return out;
}

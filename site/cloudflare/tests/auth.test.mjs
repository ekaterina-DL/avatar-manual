// Проверки входа: node --test site/cloudflare/tests
// База — настоящий SQLite в памяти (node:sqlite) с той же схемой, что в D1.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";
import {
  handle, hashPassword, verifyPassword, signSession, readSession, canAccess, safeNext,
  COOKIE, MAX_FAILS, LOCK_MINUTES, SESSION_DAYS,
} from "../lib/auth.js";

const SCHEMA = readFileSync(new URL("../schema.sql", import.meta.url), "utf8");
const SECRET = "x".repeat(48);
const T0 = 1_800_000_000_000;

function d1(db) {
  return {
    prepare(sql) {
      let args = [];
      const stmt = {
        bind(...a) { args = a; return stmt; },
        async first() { return db.prepare(sql).get(...args) ?? null; },
        async run() { db.prepare(sql).run(...args); return { success: true }; },
        async all() { return { results: db.prepare(sql).all(...args) }; },
      };
      return stmt;
    },
  };
}

async function setup(users = [["Assessor1", "Pass-word-1", "stage2"]]) {
  const db = new DatabaseSync(":memory:");
  db.exec(SCHEMA);
  for (const [login, pw, groups, active = 1] of users) {
    db.prepare("INSERT INTO users (login, pw, groups, active, created) VALUES (?, ?, ?, ?, ?)")
      .run(login, await hashPassword(pw), groups, active, T0);
  }
  return { db, env: { DB: d1(db), SESSION_SECRET: SECRET } };
}

const passthrough = async () => new Response("SECRET CONTENT", { headers: { "Cache-Control": "public, max-age=0" } });
const noWait = () => {};

function req(path, { method = "GET", cookie, form } = {}) {
  const init = { method, headers: {} };
  if (cookie) init.headers.Cookie = `${COOKIE}=${cookie}`;
  if (form) init.body = new URLSearchParams(form);
  return new Request(`https://site.test${path}`, init);
}

async function login(env, loginName, password, now = T0, next = "/") {
  return handle(req("/__login", { method: "POST", form: { login: loginName, password, next } }), env, passthrough, noWait, now);
}

function cookieFrom(res) {
  const m = /__Host-s=([^;]*)/.exec(res.headers.get("Set-Cookie") || "");
  return m ? m[1] : null;
}

test("пароль: хэш проверяется, чужой пароль нет", async () => {
  const h = await hashPassword("abc-DEF-123");
  assert.ok(h.startsWith("pbkdf2$"));
  assert.equal(await verifyPassword("abc-DEF-123", h), true);
  assert.equal(await verifyPassword("abc-DEF-124", h), false);
  assert.equal(await verifyPassword("x", "мусор"), false);
});

test("без входа: любая страница и файл уводят на вход, содержимое не отдаётся", async () => {
  const { env } = await setup();
  for (const p of ["/", "/manual-2-etap/00-overview/", "/manual-2-etap/assets/a.mp4", "/search/search_index.json", "/assessor-helper/rules.json"]) {
    const res = await handle(req(p), env, passthrough, noWait, T0);
    assert.equal(res.status, 303, p);
    assert.match(res.headers.get("Location"), /^\/__login\?next=/);
    assert.doesNotMatch(await res.text(), /SECRET CONTENT/);
  }
});

test("POST без входа получает 401", async () => {
  const { env } = await setup();
  const res = await handle(req("/x", { method: "POST" }), env, passthrough, noWait, T0);
  assert.equal(res.status, 401);
});

test("верный логин и пароль: сеанс на 14 дней, доступ к сайту", async () => {
  const { env, db } = await setup();
  const res = await login(env, "Assessor1", "Pass-word-1", T0, "/manual-2-etap/");
  assert.equal(res.status, 303);
  assert.equal(res.headers.get("Location"), "/manual-2-etap/");
  const sc = res.headers.get("Set-Cookie");
  assert.match(sc, /HttpOnly/); assert.match(sc, /Secure/); assert.match(sc, new RegExp(`Max-Age=${SESSION_DAYS * 86400}`));
  const page = await handle(req("/manual-2-etap/", { cookie: cookieFrom(res) }), env, passthrough, noWait, T0 + 1000);
  assert.equal(page.status, 200);
  assert.equal(await page.text(), "SECRET CONTENT");
  assert.match(page.headers.get("Cache-Control"), /private/);
  assert.equal(db.prepare("SELECT kind FROM events WHERE kind='login_ok'").all().length, 1);
});

test("логин без учёта регистра букв", async () => {
  const { env } = await setup();
  assert.equal((await login(env, "assessor1", "Pass-word-1")).status, 303);
});

test("сеанс истекает через 14 дней", async () => {
  const { env } = await setup();
  const c = cookieFrom(await login(env, "Assessor1", "Pass-word-1"));
  const late = await handle(req("/", { cookie: c }), env, passthrough, noWait, T0 + SESSION_DAYS * 86400000 + 1);
  assert.equal(late.status, 303);
});

test("неверный пароль и несуществующий логин дают одинаковый ответ", async () => {
  const { env } = await setup();
  const a = await login(env, "Assessor1", "wrong");
  const b = await login(env, "Nobody", "wrong");
  assert.equal(a.status, 401); assert.equal(b.status, 401);
  assert.match(await a.text(), /Неверный логин или пароль/);
  assert.match(await b.text(), /Неверный логин или пароль/);
  assert.equal(a.headers.get("Set-Cookie"), null);
});

test(`после ${MAX_FAILS} неверных паролей логин блокируется на ${LOCK_MINUTES} мин, даже верный пароль не пускает`, async () => {
  const { env } = await setup();
  for (let i = 0; i < MAX_FAILS; i++) assert.equal((await login(env, "Assessor1", "bad", T0 + i)).status, 401);
  const locked = await login(env, "Assessor1", "Pass-word-1", T0 + 10);
  assert.equal(locked.status, 429);
  assert.equal(locked.headers.get("Set-Cookie"), null);
  const after = await login(env, "Assessor1", "Pass-word-1", T0 + LOCK_MINUTES * 60000 + 100);
  assert.equal(after.status, 303);
});

test("заблокированный пользователь не входит даже с верным паролем", async () => {
  const { env } = await setup([["Assessor2", "Pass-word-2", "stage2", 0]]);
  assert.equal((await login(env, "Assessor2", "Pass-word-2")).status, 401);
});

test("блокировка и сброс сеанса выкидывают уже вошедшего сразу", async () => {
  const { env, db } = await setup();
  const c = cookieFrom(await login(env, "Assessor1", "Pass-word-1"));
  db.prepare("UPDATE users SET active = 0, sv = sv + 1 WHERE login = 'Assessor1'").run();
  assert.equal((await handle(req("/", { cookie: c }), env, passthrough, noWait, T0 + 1)).status, 303);
  db.prepare("UPDATE users SET active = 1 WHERE login = 'Assessor1'").run();
  // старый сеанс остаётся недействительным, нужен новый вход
  assert.equal((await handle(req("/", { cookie: c }), env, passthrough, noWait, T0 + 2)).status, 303);
});

test("подделанный или чужой подписью сеанс не пускает", async () => {
  const { env } = await setup();
  const forged = await signSession({ l: "Assessor1", v: 1, e: T0 + 1e9 }, "y".repeat(48));
  assert.equal((await handle(req("/", { cookie: forged }), env, passthrough, noWait, T0)).status, 303);
  const good = cookieFrom(await login(env, "Assessor1", "Pass-word-1"));
  const [body, sig] = good.split(".");
  const tampered = Buffer.from(body, "base64url").toString().replace("Assessor1", "Admin");
  const bad = `${Buffer.from(tampered).toString("base64url")}.${sig}`;
  assert.equal((await handle(req("/", { cookie: bad }), env, passthrough, noWait, T0)).status, 303);
  assert.equal(await readSession("мусор", SECRET, T0), null);
});

test("роли: 3 этап только для stage3 и admin", async () => {
  assert.equal(canAccess("stage2", "/manual-3-etap/00-overview/"), false);
  assert.equal(canAccess("stage2,stage3", "/manual-3-etap/00-overview/"), true);
  assert.equal(canAccess("admin", "/manual-3-etap/"), true);
  assert.equal(canAccess("stage2", "/manual-2-etap/"), true);
  const { env } = await setup();
  const c = cookieFrom(await login(env, "Assessor1", "Pass-word-1"));
  assert.equal((await handle(req("/manual-3-etap/x/", { cookie: c }), env, passthrough, noWait, T0)).status, 403);
});

test("выход гасит сеанс в браузере", async () => {
  const { env } = await setup();
  const c = cookieFrom(await login(env, "Assessor1", "Pass-word-1"));
  const out = await handle(req("/__logout", { cookie: c }), env, passthrough, noWait, T0);
  assert.equal(out.status, 303);
  assert.match(out.headers.get("Set-Cookie"), /Max-Age=0/);
});

test("после входа возвращаем только на страницы этого сайта", () => {
  assert.equal(safeNext("/manual-2-etap/"), "/manual-2-etap/");
  assert.equal(safeNext("https://evil.example/"), "/");
  assert.equal(safeNext("//evil.example/"), "/");
  assert.equal(safeNext("/\\evil.example"), "/");
  assert.equal(safeNext("/__login"), "/");
});

test("страница входа экранирует next и не содержит названий проекта", async () => {
  const { env } = await setup();
  const res = await handle(req('/__login?next=/"><script>alert(1)</script>'), env, passthrough, noWait, T0);
  const html = await res.text();
  assert.doesNotMatch(html, /<script>/);
  assert.doesNotMatch(html, /Аватар|Tagme|Data ?Light|Сбер/i);
});

test("видео: запрос части файла получает ровно эту часть (206), без входа ничего", async () => {
  const { env } = await setup();
  const data = new Uint8Array(1000).map((_, i) => i % 256);
  // хранилище отдаёт файл кусками по 300 байт и игнорирует Range — как Pages за функцией
  const video = async () => new Response(new ReadableStream({
    start(c) { for (let i = 0; i < data.length; i += 300) c.enqueue(data.slice(i, i + 300)); c.close(); },
  }), { headers: { "Content-Type": "video/mp4", "Content-Length": "1000" } });
  const c = cookieFrom(await login(env, "Assessor1", "Pass-word-1"));
  const get = (range) => {
    const r = req("/manual-2-etap/assets/a.mp4", { cookie: c });
    if (range) r.headers.set("Range", range);
    return handle(r, env, video, noWait, T0);
  };
  const mid = await get("bytes=250-649");
  assert.equal(mid.status, 206);
  assert.equal(mid.headers.get("Content-Range"), "bytes 250-649/1000");
  assert.deepEqual(new Uint8Array(await mid.arrayBuffer()), data.slice(250, 650));
  const open = await get("bytes=900-");
  assert.deepEqual(new Uint8Array(await open.arrayBuffer()), data.slice(900));
  const tail = await get("bytes=-10");
  assert.equal(tail.headers.get("Content-Range"), "bytes 990-999/1000");
  assert.equal((await get("bytes=5000-")).status, 416);
  const full = await get(null);
  assert.equal(full.status, 200);
  assert.equal(full.headers.get("Accept-Ranges"), "bytes");
  // хранилище без Content-Length: кусок всё равно вырезается верно
  const noLen = async () => new Response(new ReadableStream({ start(c) { c.enqueue(data); c.close(); } }), { headers: { "Content-Type": "video/mp4" } });
  const r2 = req("/manual-2-etap/assets/a.mp4", { cookie: c });
  r2.headers.set("Range", "bytes=10-19");
  const part = await handle(r2, env, noLen, noWait, T0);
  assert.equal(part.status, 206);
  assert.equal(part.headers.get("Content-Range"), "bytes 10-19/1000");
  assert.deepEqual(new Uint8Array(await part.arrayBuffer()), data.slice(10, 20));
  const anon = await handle((() => { const r = req("/manual-2-etap/assets/a.mp4"); r.headers.set("Range", "bytes=0-9"); return r; })(), env, video, noWait, T0);
  assert.equal(anon.status, 303);
});

const ADMIN_KEY = "k".repeat(48);
function admin(env, payload, key = ADMIN_KEY) {
  const r = new Request("https://site.test/__admin", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle(r, env, passthrough, noWait, T0);
}

test("управление из таблицы: без ключа или с чужим ключом ничего нельзя", async () => {
  const { env } = await setup();
  env.ADMIN_KEY = ADMIN_KEY;
  assert.equal((await admin(env, { action: "list" }, "wrong".repeat(10))).status, 403);
  assert.equal((await admin(env, { action: "list" }, "")).status, 403);
  const noKeyEnv = { ...env, ADMIN_KEY: undefined };
  assert.equal((await admin(noKeyEnv, { action: "list" })).status, 403);
  const get = await handle(new Request("https://site.test/__admin"), env, passthrough, noWait, T0);
  assert.equal(get.status, 405);
});

test("управление из таблицы: выдать следующий логин, сбросить, заблокировать", async () => {
  const { env, db } = await setup([["Assessor1", "Pass-word-1", "stage2"], ["Assessor7", "x-x-x-x-1", "stage2"]]);
  env.ADMIN_KEY = ADMIN_KEY;
  const added = await (await admin(env, { action: "add" })).json();
  assert.equal(added.login, "Assessor8");
  assert.match(added.password, /^[A-Za-z2-9]{12}$/);
  assert.equal((await login(env, "Assessor8", added.password)).status, 303);
  assert.equal((await admin(env, { action: "add", login: "Assessor8" })).status, 409);

  const c = cookieFrom(await login(env, "Assessor1", "Pass-word-1"));
  const reset = await (await admin(env, { action: "reset", login: "assessor1" })).json();
  assert.equal(reset.login, "Assessor1");
  assert.equal((await handle(req("/", { cookie: c }), env, passthrough, noWait, T0)).status, 303); // старый вход погас
  assert.equal((await login(env, "Assessor1", "Pass-word-1")).status, 401);
  assert.equal((await login(env, "Assessor1", reset.password)).status, 303);

  assert.equal((await admin(env, { action: "block", login: "Assessor8" })).status, 200);
  assert.equal((await login(env, "Assessor8", added.password)).status, 401);
  assert.equal((await admin(env, { action: "unblock", login: "Assessor8" })).status, 200);
  assert.equal((await login(env, "Assessor8", added.password)).status, 303);

  assert.equal((await admin(env, { action: "block", login: "Nobody" })).status, 404);
  assert.equal((await admin(env, { action: "add", login: "bad login!" })).status, 400);
  const list = await (await admin(env, { action: "list" })).json();
  assert.deepEqual(list.users.map((u) => u.login), ["Assessor1", "Assessor7", "Assessor8"]);
  assert.ok(db.prepare("SELECT * FROM events WHERE kind = 'admin_add'").all().length === 1);
  assert.ok(!JSON.stringify(list).includes("pbkdf2"));
});

test("управление из таблицы: журнал за N дней, свежие сверху, старые не попадают", async () => {
  const { env, db } = await setup();
  env.ADMIN_KEY = ADMIN_KEY;
  const day = 86400000;
  for (const [ago, kind] of [[1, "login_ok"], [5, "view"], [20, "login_fail"], [100, "logout"]]) {
    db.prepare("INSERT INTO events (ts, login, kind, path) VALUES (?, 'Assessor1', ?, NULL)").run(T0 - ago * day, kind);
  }
  const week = await (await admin(env, { action: "log", days: 7 })).json();
  assert.deepEqual(week.events.map((e) => e.kind), ["login_ok", "view"]);
  const month = await (await admin(env, { action: "log", days: 30 })).json();
  assert.equal(month.events.length, 3);
  const all = await (await admin(env, { action: "log", days: 180 })).json();
  assert.equal(all.events.length, 4);
  assert.equal(all.truncated, false);
  assert.equal((await admin(env, { action: "log", days: 7 }, "bad".repeat(20))).status, 403);
});

test("просмотры страниц пишутся в журнал, файлы нет", async () => {
  const { env, db } = await setup();
  const c = cookieFrom(await login(env, "Assessor1", "Pass-word-1"));
  const pending = [];
  const wait = (p) => pending.push(p);
  await handle(req("/manual-2-etap/", { cookie: c }), env, passthrough, wait, T0);
  await handle(req("/manual-2-etap/assets/a.mp4", { cookie: c }), env, passthrough, wait, T0);
  await Promise.all(pending);
  const views = db.prepare("SELECT path FROM events WHERE kind='view'").all();
  assert.deepEqual(views.map((v) => v.path), ["/manual-2-etap/"]);
});

// Управление логинами сайта (база D1 manual-auth на Cloudflare). Запуск с компьютера Екатерины,
// после `npx wrangler login`. Пароли показываются ОДИН раз — в базе только их хэши.
//
//   node site/cloudflare/users.mjs add Assessor1 [группы]     новый логин (группы: stage2 по умолчанию)
//   node site/cloudflare/users.mjs add-range 1 30 [группы]    Assessor1 ... Assessor30
//   node site/cloudflare/users.mjs reset Assessor1             новый пароль, старые входы гаснут
//   node site/cloudflare/users.mjs block Assessor1             заблокировать, выкинуть с сайта сразу
//   node site/cloudflare/users.mjs unblock Assessor1           разблокировать (пароль прежний)
//   node site/cloudflare/users.mjs groups Assessor1 stage2,stage3
//   node site/cloudflare/users.mjs list                        все логины
//   node site/cloudflare/users.mjs log [дней=7]                журнал входов и просмотров
import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { hashPassword } from "./lib/auth.js";

const DB = "manual-auth";
const WRANGLER = ["--yes", "wrangler@3.112.0"];
const LOGIN_RE = /^[A-Za-z0-9_-]{1,40}$/;
const GROUPS_RE = /^[a-z0-9]+(,[a-z0-9]+)*$/;
// Без похожих символов (0/O, 1/l/I), чтобы пароль легко перепечатать.
const ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789";

// npx запускаем через node без оболочки: так SQL-команда доходит одним аргументом
// (в Windows через оболочку она разбивается по пробелам).
function npx(args) {
  const cli = join(dirname(process.execPath), "node_modules", "npm", "bin", "npx-cli.js");
  if (existsSync(cli)) return execFileSync(process.execPath, [cli, ...args], OPTS);
  return execFileSync("npx", args, OPTS);
}
const OPTS = { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"], maxBuffer: 64 * 1024 * 1024 };

function sql(command) {
  const out = npx([...WRANGLER, "d1", "execute", DB, "--remote", "--json", "--command", command]);
  const data = JSON.parse(out.slice(out.indexOf("[")));
  return data.flatMap((r) => r.results || []);
}

function q(s) {
  return `'${String(s).replace(/'/g, "''")}'`;
}

function newPassword(len = 12) {
  // Отбрасываем байты сверх кратного длине алфавита, чтобы все символы были равновероятны.
  const limit = 256 - (256 % ALPHABET.length);
  let out = "";
  while (out.length < len) {
    for (const b of crypto.getRandomValues(new Uint8Array(len * 2))) {
      if (b < limit && out.length < len) out += ALPHABET[b % ALPHABET.length];
    }
  }
  return out;
}

function checkLogin(login) {
  if (!LOGIN_RE.test(login || "")) throw new Error(`Плохой логин: ${login}`);
  return login;
}

function checkGroups(groups) {
  if (!GROUPS_RE.test(groups)) throw new Error(`Плохие группы: ${groups} (пример: stage2 или stage2,stage3)`);
  return groups;
}

async function add(logins, groups) {
  const rows = [];
  const values = [];
  for (const login of logins) {
    const pw = newPassword();
    values.push(`(${q(checkLogin(login))}, ${q(await hashPassword(pw))}, ${q(groups)}, ${Date.now()})`);
    rows.push([login, pw]);
  }
  sql(`INSERT INTO users (login, pw, groups, created) VALUES ${values.join(", ")}`);
  console.log("Логин\tПароль");
  for (const [l, p] of rows) console.log(`${l}\t${p}`);
  console.log("\nСохраните пароли сейчас: повторно их не показать, только сбросить (reset).");
}

const fmt = (ms) => (ms ? new Date(ms).toLocaleString("ru-RU", { timeZone: "Europe/Moscow" }) : "");

async function main() {
  const [cmd, a, b, c] = process.argv.slice(2);
  switch (cmd) {
    case "add":
      return add([a], checkGroups(b || "stage2"));
    case "add-range": {
      const from = Number(a), to = Number(b);
      if (!(from >= 1 && to >= from && to - from < 200)) throw new Error("Пример: add-range 1 30");
      const logins = [];
      for (let i = from; i <= to; i++) logins.push(`Assessor${i}`);
      return add(logins, checkGroups(c || "stage2"));
    }
    case "reset": {
      const pw = newPassword();
      sql(`UPDATE users SET pw = ${q(await hashPassword(pw))}, sv = sv + 1, fails = 0, locked_until = 0 WHERE login = ${q(checkLogin(a))}`);
      console.log(`${a}\t${pw}\n\nСтарые входы этого логина больше не действуют.`);
      return;
    }
    case "block":
      sql(`UPDATE users SET active = 0, sv = sv + 1 WHERE login = ${q(checkLogin(a))}`);
      return console.log(`${a} заблокирован, открытые входы закрыты.`);
    case "unblock":
      sql(`UPDATE users SET active = 1, fails = 0, locked_until = 0 WHERE login = ${q(checkLogin(a))}`);
      return console.log(`${a} разблокирован.`);
    case "groups":
      sql(`UPDATE users SET groups = ${q(checkGroups(b))}, sv = sv + 1 WHERE login = ${q(checkLogin(a))}`);
      return console.log(`${a}: группы ${b}.`);
    case "list": {
      const rows = sql("SELECT login, groups, active, locked_until, created FROM users ORDER BY created, login");
      console.log("Логин\tГруппы\tСтатус\tСоздан");
      for (const r of rows) {
        const status = !r.active ? "заблокирован" : r.locked_until > Date.now() ? "пауза после неверных паролей" : "активен";
        console.log(`${r.login}\t${r.groups}\t${status}\t${fmt(r.created)}`);
      }
      return;
    }
    case "log": {
      const days = Number(a || 7);
      const rows = sql(`SELECT ts, login, kind, path FROM events WHERE ts > ${Date.now() - days * 86400000} ORDER BY ts DESC LIMIT 500`);
      for (const r of rows) console.log(`${fmt(r.ts)}\t${r.login}\t${r.kind}\t${r.path || ""}`);
      return;
    }
    default:
      console.log("Команды: add, add-range, reset, block, unblock, groups, list, log (см. начало файла).");
  }
}

main().catch((e) => {
  console.error(e.message || e);
  process.exit(1);
});

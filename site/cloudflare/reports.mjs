// Загрузка презентаций созвонов на закрытый сайт (хранилище KV manual-reports, привязка REPORTS).
// Презентации лежат только на компьютере: _raw-sources/reports/<папка>/index.html (+ assets/...).
// На GitHub они не попадают. На сайте открываются по адресу /reports/<папка>/ после входа.
//
//   node site/cloudflare/reports.mjs upload <папка>     загрузить (или обновить) одну презентацию
//   node site/cloudflare/reports.mjs list                что уже загружено
//   node site/cloudflare/reports.mjs remove <папка>      убрать с сайта
//
// Ссылки на старый открытый мануал (github.io) при загрузке заменяются на ссылки закрытого сайта.
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync, statSync, writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { dirname, join, relative, sep } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";

const NAMESPACE_ID = "3efd21b72f1f48148eca0dfc2b4f01fd";
const WRANGLER = ["--yes", "wrangler@3.112.0"];
const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "_raw-sources", "reports");
const MAX_BYTES = 25 * 1024 * 1024;
const NAME_RE = /^[a-z0-9][a-z0-9-]*$/;
const OLD_SITE = /https:\/\/ekaterina-dl\.github\.io\/avatar-manual\//gi;

function npx(args) {
  const cli = join(dirname(process.execPath), "node_modules", "npm", "bin", "npx-cli.js");
  const opts = { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"], maxBuffer: 64 * 1024 * 1024 };
  return existsSync(cli) ? execFileSync(process.execPath, [cli, ...args], opts) : execFileSync("npx", args, opts);
}

function walk(dir) {
  return readdirSync(dir).flatMap((n) => {
    const p = join(dir, n);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
}

function upload(name) {
  if (!NAME_RE.test(name || "")) throw new Error("Имя папки: латиница, цифры и дефисы, например sozvon-2026-11-20");
  const dir = join(ROOT, name);
  if (!existsSync(join(dir, "index.html"))) throw new Error(`Нет файла ${join(dir, "index.html")}`);
  const tmp = mkdtempSync(join(tmpdir(), "report-"));
  const entries = [];
  try {
    for (const file of walk(dir)) {
      const rel = relative(dir, file).split(sep).join("/");
      const size = statSync(file).size;
      if (size > MAX_BYTES) throw new Error(`${rel}: ${Math.round(size / 1048576)} МБ, больше 25 МБ — сожмите файл`);
      let path = file;
      if (rel.endsWith(".html")) {
        const html = readFileSync(file, "utf8").replace(OLD_SITE, "/");
        path = join(tmp, rel.replace(/\//g, "_"));
        writeFileSync(path, html);
      }
      entries.push([`${name}/${rel}`, path]);
    }
    for (const [key, path] of entries) {
      npx([...WRANGLER, "kv", "key", "put", key, "--path", path, "--namespace-id", NAMESPACE_ID]);
      console.log(`загружено: /reports/${key}`);
    }
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
  console.log(`\nГотово: https://avatar-manual.pages.dev/reports/${name}/`);
}

function keys() {
  const out = npx([...WRANGLER, "kv", "key", "list", "--namespace-id", NAMESPACE_ID]);
  return JSON.parse(out.slice(out.indexOf("["))).map((k) => k.name);
}

const [cmd, arg] = process.argv.slice(2);
try {
  if (cmd === "upload") upload(arg);
  else if (cmd === "list") {
    const byFolder = {};
    for (const k of keys()) (byFolder[k.split("/")[0]] ||= []).push(k);
    for (const [f, ks] of Object.entries(byFolder)) console.log(`/reports/${f}/  (${ks.length} файл.)`);
  } else if (cmd === "remove") {
    if (!NAME_RE.test(arg || "")) throw new Error("Укажите папку");
    for (const k of keys().filter((k) => k.startsWith(`${arg}/`))) {
      npx([...WRANGLER, "kv", "key", "delete", k, "--namespace-id", NAMESPACE_ID]);
      console.log(`удалено: /reports/${k}`);
    }
  } else console.log("Команды: upload <папка>, list, remove <папка> (см. начало файла).");
} catch (e) {
  console.error(e.message || e);
  process.exit(1);
}

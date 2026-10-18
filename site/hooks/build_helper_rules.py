"""Хук: собирает rules.json для программы «Помощник асессора» (assessor-helper/).

Для каждой проверки программы (check_id) файл assessor-helper/rules-map.yml говорит, какой
раздел мануала к ней относится: страница + заголовок (+ необязательно `contains` - взять из
раздела только абзацы/пункты списка с этой подстрокой, и `occurrence` - какой по счёту
одноимённый заголовок на странице). Хук берёт текст раздела ДОСЛОВНО (только убирает разметку:
HTML-теги, `{: …}`, звёздочки, картинки), собирает примеры-видео из ссылок раздела и пишет
<site_dir>/assessor-helper/rules.json + version.json. Своих формулировок не добавляет.

Заголовок не найден (раздел переименовали) -> PluginError с именем check_id: сборка падает и
показывает, что поправить в rules-map.yml, чтобы программа не показала пустое правило.
Якорь (#…) считается тем же slugify, что в site/mkdocs.yml (как в build_quiz_bank.py), с учётом
повторов на странице (как toc: рамка, рамка_1, …); после сборки якорь сверяется с готовым HTML.

На PDF-профиле ничего не делает.
"""

import datetime
import html
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import yaml
from markdown.extensions.toc import unique
from mkdocs.exceptions import PluginError
from pymdownx.slugs import slugify as _slugify_factory

from _build_profile import is_pdf_build
from _section_utils import extract_section

BASE_URL = "https://ekaterina-dl.github.io/avatar-manual/"
DOWNLOAD_URL = "https://github.com/ekaterina-DL/avatar-manual/releases/latest"
MAP_PATH = "assessor-helper/rules-map.yml"
VERSION_PATH = "assessor-helper/helper/version.py"
OUT_DIR = "assessor-helper"

_heading_slug = _slugify_factory(case="lower")

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_ATTR_RE = re.compile(r"\s*\{:[^}]*\}")
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_AUTOLINK_RE = re.compile(r"<(https?://[^>\s]+)>")
_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]*)\)")
_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")
_LIST_RE = re.compile(r"^([-*+]|\d+\.)(?:\s+(.*))?$")
_TABLE_SEP_RE = re.compile(r"^\|?\s*:?-{3,}")
_VIDEO_HOSTS = ("youtube.com", "youtu.be", "vk.com", "vkvideo.ru")


# --- текст раздела -> простой текст ---

def _clean_inline(s):
    s = _IMAGE_RE.sub("", s)
    s = _AUTOLINK_RE.sub(r"\1", s)
    s = _LINK_RE.sub(r"\1", s)
    s = _ATTR_RE.sub("", s)
    s = re.sub(r"</span>(?=\S)", " ", s)
    s = _TAG_RE.sub("", s)
    s = html.unescape(s)
    s = s.replace("`", "").replace("*", "")
    return re.sub(r"\s+", " ", s).strip()


def _is_video(url):
    p = urlparse(url)
    if re.search(r"\.mp4$", p.path, re.I):
        return True
    host = p.netloc.lower()
    return any(host == h or host.endswith("." + h) for h in _VIDEO_HOSTS)


def _abs_url(url, page):
    if urlparse(url).scheme:
        return url
    return urljoin(BASE_URL + page.rsplit("/", 1)[0] + "/", url) if "/" in page \
        else urljoin(BASE_URL, url)


def _examples(raw, page):
    out = []
    for title, url in _LINK_RE.findall(_IMAGE_RE.sub("", raw)):
        if url and _is_video(url):
            out.append({"title": _clean_inline(title) or "Пример",
                        "url": _abs_url(url, page)})
    return out


def _raw_blocks(md):
    """[(kind, marker, raw_text)]: kind = p (абзац) | li (пункт списка) | row (строка таблицы)
    | h (подзаголовок внутри раздела)."""
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    md = re.sub(r"<li\b[^>]*>", "\n- ", md)
    md = re.sub(r"</li>", "\n", md)
    md = re.sub(r"</?(?:ul|ol|div|p|table|br)\b[^>]*>", "\n\n", md)
    blocks, cur = [], None

    def close():
        nonlocal cur
        if cur:
            blocks.append((cur[0], cur[1], " ".join(cur[2])))
        cur = None

    for line in md.split("\n"):
        s = line.strip()
        while s.startswith(">"):
            s = s[1:].strip()
        if not s:
            # <li markdown="1"> + пустая строка + текст пункта: пункт ещё не начался
            if not (cur and cur[0] == "li" and not "".join(cur[2]).strip()):
                close()
            continue
        m = _HEADING_RE.match(s)
        if m:
            close()
            blocks.append(("h", None, m.group(2)))
            continue
        if s.startswith("|"):
            close()
            cells = [_clean_inline(c) for c in s.strip().strip("|").split("|")]
            if not _TABLE_SEP_RE.match(s) and any(cells):
                blocks.append(("row", None, " | ".join(cells)))
            continue
        m = _LIST_RE.match(s)
        if m:
            close()
            marker = "-" if m.group(1) in "-*+" else m.group(1)
            cur = ["li", marker, [m.group(2) or ""]]
            continue
        if cur is None:
            cur = ["p", None, [s]]
        else:
            cur[2].append(s)
    close()
    return blocks


def _blocks(md, page):
    """[{kind, text, match, examples, show, src}].
    show=False - блок не идёт в текст правила: пустой после чистки (картинка, обёртка HTML) или
    пункт списка, который целиком - ссылка на видео (он уже есть в examples)."""
    out = []
    for kind, marker, raw in _raw_blocks(md):
        text = _clean_inline(raw)
        examples = _examples(raw, page)
        video_only = (kind == "li" and bool(examples)
                      and bool(re.fullmatch(r"\[[^\]]*\]\([^)\s]+\)\.?", raw.strip())))
        out.append({
            "kind": kind,
            "text": f"{marker} {text}" if kind == "li" else text,
            "match": text.lower() or " ".join(e["title"] for e in examples).lower(),
            "examples": examples,
            "show": bool(text) and not video_only,
            # блок - только пометка-источник `[…]`
            "src": bool(re.fullmatch(r"`?\[[^\]]*\]`?", raw.strip())),
        })
    return out


def _visible(blocks):
    """Блоки для текста; без «висящих» вводных строк «…:», чей список ушёл в examples, и без
    пометок-источников, которые относятся к такому списку (идут сразу за скрытым блоком)."""
    out = []
    for i, b in enumerate(blocks):
        prev = blocks[i - 1] if i > 0 else None
        nxt = blocks[i + 1] if i + 1 < len(blocks) else None
        if not b["show"]:
            continue
        if b["src"] and prev is not None and not prev["show"]:
            continue
        if b["text"].endswith(":") and (nxt is None or not nxt["show"]):
            continue
        out.append(b)
    return out


def _join(blocks):
    parts = []
    prev = None
    for b in blocks:
        if parts:
            same_list = b["kind"] == prev == "li" or b["kind"] == prev == "row"
            parts.append("\n" if same_list else "\n\n")
        parts.append(b["text"])
        prev = b["kind"]
    return "".join(parts)


def section_to_text(md, page, contains=None):
    """Текст раздела (дословно, без разметки) и примеры-видео [{title, url}].
    contains (строка или список) - оставить только блоки с этой подстрокой (без учёта регистра)
    и идущую сразу за ними пометку-источник. Ничего не подошло -> ("", [])."""
    blocks = _blocks(md, page)
    if contains:
        needles = [contains] if isinstance(contains, str) else list(contains)
        needles = [n.lower() for n in needles]
        picked, take_src = [], False
        for b in blocks:
            if any(n in b["match"] for n in needles):
                picked.append(b)
                take_src = True
            elif take_src and b["src"]:
                picked.append(b)
                take_src = False
            else:
                take_src = False
        blocks = picked
    if not blocks:
        return "", []
    examples, seen = [], set()
    for b in blocks:
        for e in b["examples"]:
            if e["url"] not in seen:
                seen.add(e["url"])
                examples.append(e)
    visible = _visible(blocks)
    return _join(visible), examples


# --- заголовки и якоря ---

def _heading_text(raw):
    return _clean_inline(_ATTR_RE.sub("", raw))


def _find_heading(text, heading, occurrence=1):
    """(индекс строки, сырой текст заголовка, якорь) или None. Якорь - как у toc: slug с
    суффиксом _1, _2… для повторов на странице."""
    ids, seen, in_code = set(), 0, False
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        m = _HEADING_RE.match(line)
        if in_code or not m:
            continue
        clean = _heading_text(m.group(2))
        anchor = unique(_heading_slug(clean, "-"), ids)
        if clean == heading:
            seen += 1
            if seen == occurrence:
                return i, m.group(2), anchor
    return None


def _page_url(page):
    path = page[:-3] if page.endswith(".md") else page
    if path == "index" or path.endswith("/index"):
        path = path[:-5]
    else:
        path += "/"
    return BASE_URL + path


def _section(docs_dir, check_id, page, heading, occurrence=1):
    """(тело раздела, якорь); нет страницы/заголовка -> PluginError с check_id."""
    src = Path(docs_dir) / page
    if not src.is_file():
        raise PluginError(f"build_helper_rules: {check_id}: нет страницы {page}")
    text = src.read_text(encoding="utf-8")
    found = _find_heading(text, heading, occurrence)
    if found is None:
        raise PluginError(f"build_helper_rules: {check_id}: на странице {page} нет "
                          f"заголовка «{heading}» - поправьте {MAP_PATH}")
    idx, raw_heading, anchor = found
    return extract_section("\n".join(text.split("\n")[idx:]), raw_heading), anchor


def _as_list(value):
    if value is None:
        return []
    return [value] if isinstance(value, (str, dict)) else list(value)


def build_rules(docs_dir, rules_map):
    """heading - строка или список (тексты разделов идут подряд, примеры объединяются, ссылка -
    на первый раздел). examples_from - [{page?, heading, contains?}]: добавить примеры из другого
    раздела (contains фильтрует подписи примеров), их текст в правило не идёт."""
    docs_dir = Path(docs_dir)
    rules = {}
    for check_id, entry in rules_map.items():
        page = entry["page"]
        texts, examples, url = [], [], None
        for heading in _as_list(entry["heading"]):
            body, anchor = _section(docs_dir, check_id, page, heading,
                                    entry.get("occurrence", 1))
            url = url or f"{_page_url(page)}#{anchor}"
            part, ex = section_to_text(body, page, entry.get("contains"))
            if part:
                texts.append(part)
            examples += ex
        if not texts:
            raise PluginError(f"build_helper_rules: {check_id}: в разделе «{entry['heading']}» "
                              f"({page}) нет текста" + (f" с «{entry['contains']}»"
                                                        if entry.get("contains") else ""))
        for extra in _as_list(entry.get("examples_from")):
            xpage = extra.get("page", page)
            body, _ = _section(docs_dir, check_id, xpage, extra["heading"])
            _, ex = section_to_text(body, xpage)
            needle = (extra.get("contains") or "").lower()
            picked = [e for e in ex if needle in e["title"].lower()]
            if not picked:
                raise PluginError(f"build_helper_rules: {check_id}: examples_from «{extra}» - "
                                  f"нет подходящих примеров")
            examples += picked
        seen, uniq = set(), []
        for e in examples:
            if e["url"] not in seen:
                seen.add(e["url"])
                uniq.append(e)
        rules[check_id] = {
            "title": entry["title"],
            "text": "\n\n".join(texts),
            "url": url,
            "examples": uniq,
        }
    return rules


def load_rules_map(root):
    path = Path(root) / MAP_PATH
    if not path.is_file():
        raise PluginError(f"build_helper_rules: нет файла {MAP_PATH} (соответствие проверок "
                          f"программы разделам мануала) в {root}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data:
        raise PluginError(f"build_helper_rules: {MAP_PATH} пустой или не словарь")
    return data


def read_version(root):
    src = (Path(root) / VERSION_PATH).read_text(encoding="utf-8")
    m = re.search(r"""^(?:__version__|VERSION)\s*=\s*["']([^"']+)["']""", src, re.M)
    if not m:
        raise PluginError(f"build_helper_rules: в {VERSION_PATH} нет номера версии")
    return m.group(1)


def _check_anchors(site_dir, rules):
    """Якорь каждого правила должен быть в готовом HTML страницы (если страница собрана)."""
    bad = []
    for check_id, r in rules.items():
        rel, anchor = r["url"][len(BASE_URL):].split("#", 1)
        page_html = site_dir / rel / "index.html"
        if page_html.is_file() and f'id="{anchor}"' not in page_html.read_text(encoding="utf-8"):
            bad.append(f"{check_id} (#{anchor})")
    if bad:
        raise PluginError("build_helper_rules: якоря не найдены в собранном сайте: "
                          + ", ".join(bad))


def on_post_build(config):
    if is_pdf_build(config):
        return
    docs_dir = Path(config["docs_dir"])
    site_dir = Path(str(config["site_dir"]))
    rules = build_rules(docs_dir, load_rules_map(docs_dir))
    _check_anchors(site_dir, rules)
    out = site_dir / OUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    (out / "rules.json").write_text(json.dumps(
        {"generated": datetime.date.today().isoformat(), "rules": rules},
        ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "version.json").write_text(json.dumps(
        {"version": read_version(docs_dir), "download": DOWNLOAD_URL},
        ensure_ascii=False, indent=1), encoding="utf-8")

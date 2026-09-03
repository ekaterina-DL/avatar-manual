import re

from _build_profile import is_public_build

# Заголовок-ссылка на главной, ведущий в мануал 3 этапа. В публичной сборке 3 этап не
# выкладывается — убираем весь относящийся к нему блок «выбора этапа», чтобы на главной не
# осталось ни битой ссылки, ни упоминания раздела, которого на сайте нет.
_INDEX_STAGE3_HEADING_RE = re.compile(r"^#{1,6}\s+\[[^\]]*\]\([^)]*manual-3-etap/[^)]*\)\s*$")
_HEADING_RE = re.compile(r"^#{1,6}\s")

# Любая markdown-ссылка, чей URL ведёт в manual-3-etap/ (в т.ч. «../manual-3-etap/...#якорь»).
# К моменту работы этого хука friendly_md_link_text.py уже мог переписать ВИДИМЫЙ текст
# ссылки — сопоставляемся только по URL. Видимый текст оставляем, саму ссылку снимаем —
# ровно как neutralize_excluded_links.py для _sources-log.md и voprosy-zakazchiku.md.
_STAGE3_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*manual-3-etap/[^)]*\)")


def _drop_index_stage3_block(markdown):
    """Убирает с index.md заголовок-ссылку на мануал 3 этапа и абзац под ним — до строки
    `---` или следующего заголовка (они остаются на месте). Если заголовка нет — без
    изменений."""
    lines = markdown.split("\n")
    out = []
    i = 0
    while i < len(lines):
        if _INDEX_STAGE3_HEADING_RE.match(lines[i]):
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() == "---" or _HEADING_RE.match(nxt):
                    break
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def on_page_markdown(markdown, page, config, files):
    """Только в публичной сборке (site/mkdocs-public.yml): скрывает следы мануала 3 этапа,
    который в этом профиле не публикуется. На обычной и PDF-сборке — no-op."""
    if not is_public_build(config):
        return markdown
    if page.file.src_uri.replace("\\", "/") == "index.md":
        markdown = _drop_index_stage3_block(markdown)
    return _STAGE3_LINK_RE.sub(lambda m: m.group(1), markdown)

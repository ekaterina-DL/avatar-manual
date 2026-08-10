import re

# Точные разовые случаи — без нечёткого сопоставления, тот же принцип, что и в
# fix_stage_relationship.py.
_REPLACEMENTS = [
    (
        "Топ-5 в 06-common-mistakes.md ссылается на те же",
        "Топ-5 в [Частые ошибки](06-common-mistakes.md) ссылается на те же",
    ),
]

_FAQ_RE = re.compile(r"см\. разбор в 07-faq\.md — ")


def on_page_markdown(markdown, page, config, files):
    """manual-2-etap/10-qa-log.md в нескольких местах упоминает 06-common-mistakes.md/
    07-faq.md голым текстом (без markdown-ссылки: просто имя файла посреди предложения) — на
    сайте это читалось как случайный обрывок имени файла. Превращает такие упоминания в
    обычные ссылки на соответствующий раздел сайта (дальше их доводит до понятного текста
    friendly_md_link_text.py); остальной текст не трогает. Сам файл мануала не меняется, без
    изменений, если исходный текст успеет разойтись с этой копией."""
    if page.file.src_uri.replace("\\", "/") != "manual-2-etap/10-qa-log.md":
        return markdown
    for old, new in _REPLACEMENTS:
        markdown = markdown.replace(old, new)
    return _FAQ_RE.sub("см. разбор в [07-faq.md](07-faq.md) — ", markdown)

import re

from _build_profile import is_pdf_build

_STATUS_RE = re.compile(
    r"^- Статус: \*\*(Решено|Частично решено|Не решено)\*\*",
    re.M,
)

_BADGE_CLASS = {
    "Решено": "status-ok",
    "Частично решено": "status-partial",
    "Не решено": "status-open",
}

_BADGE_EMOJI = {
    "Решено": "🟢",
    "Частично решено": "🟡",
    "Не решено": "🔴",
}


def _render(match):
    label = match.group(1)
    css_class = _BADGE_CLASS[label]
    emoji = _BADGE_EMOJI[label]
    return f'- <span class="status-badge {css_class}">{emoji} {label}</span>'


def on_page_markdown(markdown, page, config, files):
    """Строка "- Статус: **Решено**/**Частично решено**/**Не решено**" (канонический словарь,
    см. шапку manual-2-etap/09-disputed-points.md, "Формат записи") превращается в цветную
    плашку. Матчит только сам ярлык в начале строки — текст пояснения после него (факты, даты,
    ссылки, цитаты) не трогает. Вложенные упоминания "Статус:" не в начале bullet-а (например,
    внутри абзаца про точную границу 10:00 в разделе про макс. длину видео) не матчатся — regex
    заякорен на начало строки через re.M. PDF-профиль не трогаем: там остаётся обычный текст."""
    if is_pdf_build(config):
        return markdown
    if page.file.src_uri.replace("\\", "/") != "manual-2-etap/09-disputed-points.md":
        return markdown
    return _STATUS_RE.sub(_render, markdown)

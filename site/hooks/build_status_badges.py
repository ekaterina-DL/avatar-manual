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

_TARGET_FILES = {
    "manual-3-etap/02-open-questions.md",
}


def _render(match):
    label = match.group(1)
    css_class = _BADGE_CLASS[label]
    emoji = _BADGE_EMOJI[label]
    return f'- <span class="status-badge {css_class}">{emoji} {label}</span>'


def on_page_markdown(markdown, page, config, files):
    """Строка "- Статус: **Решено**/**Частично решено**/**Не решено**" (канонический словарь)
    превращается в цветную плашку. Матчит только сам ярлык в начале строки — текст пояснения после него (факты, даты,
    ссылки, цитаты) не трогает. Вложенные упоминания "Статус:" не в начале bullet-а не матчатся —
    regex заякорен на начало строки через re.M. Применяется к файлам из _TARGET_FILES — сама
    regex-логика файл-агностична, можно добавить новый файл при необходимости. PDF-профиль не
    трогаем: там остаётся обычный текст."""
    if is_pdf_build(config):
        return markdown
    if page.file.src_uri.replace("\\", "/") not in _TARGET_FILES:
        return markdown
    return _STATUS_RE.sub(_render, markdown)

import re

from _build_profile import is_public_build

# Метки-источники (`[Инстр. ..., стр.1]`) хук wrap_source_tags.py превращает в
# <span class="source-tag">. На сайте они скрыты CSS, но остаются в коде страницы и в поиске,
# а в их названиях есть имена компаний и каналов переписки. Поэтому в публичной сборке
# (site/mkdocs-public.yml) вырезаем их из готового HTML целиком. Локальный сайт и PDF
# сохраняют метки как есть.
_SOURCE_TAG_SPAN_RE = re.compile(r'<span class="source-tag">.*?</span>', re.DOTALL)
# Абзац, в котором кроме метки ничего не было, после вырезания становится пустым.
_EMPTY_P_RE = re.compile(r"<p>\s*</p>")


def strip_source_tags(html):
    html = _SOURCE_TAG_SPAN_RE.sub("", html)
    return _EMPTY_P_RE.sub("", html)


def on_page_content(html, page, config, files):
    """Срабатывает до того, как поиск соберёт текст страницы, поэтому метки не попадают
    и в поисковый индекс."""
    if not is_public_build(config):
        return html
    return strip_source_tags(html)

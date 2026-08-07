import re

EXCLUDED_LINK_RE = re.compile(
    r"\[([^\]]*)\]\("
    r"(?:[^)]*_sources-log\.md|[^)]*_raw-sources/[^)]*|[^)]*voprosy-zakazchiku\.md)"
    r"\)"
)


def on_page_markdown(markdown, page, config, files):
    """Markdown-ссылки на файлы, которые сознательно не публикуются на сайте
    (_sources-log.md, _raw-sources/, voprosy-zakazchiku.md — см. .gitignore в корне
    проекта), превращает в обычный текст без ссылки: на сайте ссылка была бы битой,
    хотя в самом мануале как markdown-файле вне сайта эти ссылки рабочие и корректные.
    Сам файл мануала при этом не меняется — замена происходит только на лету при сборке.
    """
    return EXCLUDED_LINK_RE.sub(lambda m: m.group(1), markdown)

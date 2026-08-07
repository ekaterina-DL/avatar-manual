import re

# Ищет `[любой текст без обратных кавычек и квадратных скобок внутри]`
SOURCE_TAG_RE = re.compile(r"`(\[[^\]\[`]+\])`")


def on_page_markdown(markdown, page, config, files):
    """Оборачивает метки-источники вида `[Инстр., стр.1]` в HTML-span
    с классом source-tag, чтобы CSS мог их прятать на сайте и показывать в PDF.
    Сам файл мануала при этом не меняется — обёртка происходит только на лету
    при сборке.
    """
    def replace(match):
        tag_text = match.group(1)
        return f'<span class="source-tag">{tag_text}</span>'

    return SOURCE_TAG_RE.sub(replace, markdown)

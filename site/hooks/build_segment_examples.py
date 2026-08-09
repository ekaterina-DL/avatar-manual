import re

from _section_utils import extract_section

TARGET_FILE = "manual-2-etap/02-segments.md"
SECTION_HEADINGS = ["Примеры (позитивные)", "Антипримеры"]

_BLOCK_START_RE = re.compile(
    r'\*\*((?:Анти)?[Пп]ример) (\d+):\*\*[ \t]*(<iframe.*?</iframe>)[ \t]*\n'
)
_IMAGE_LINE_RE = re.compile(r'!\[[^\]]*\]\([^)]+\)\n?')
_SOURCE_TAG_RE = re.compile(r'\n(`\[[^`\n]*\]`)\s*$')


def _split_blocks(section_body):
    starts = list(_BLOCK_START_RE.finditer(section_body))
    blocks = []
    for idx, match in enumerate(starts):
        block_end = starts[idx + 1].start() if idx + 1 < len(starts) else len(section_body)
        blocks.append((match, section_body[match.start():block_end]))
    return blocks


def _parse_block(match, block_text):
    kind, number, iframe_html = match.groups()
    rest = block_text[match.end() - match.start():]
    rest = _IMAGE_LINE_RE.sub("", rest, count=1)
    caption = rest.strip()
    is_bad = kind.startswith("Анти")
    return is_bad, number, iframe_html, caption


def _render_card(is_bad, number, iframe_html, caption):
    card_class = "example-card bad" if is_bad else "example-card"
    return (
        f'<div class="{card_class}">'
        f'{iframe_html}'
        '<div class="ec-body">'
        f'<span class="num">{number}</span>'
        f'<div markdown="1">{caption}</div>'
        "</div>"
        "</div>"
    )


def _transform_section(markdown, heading):
    body = extract_section(markdown, heading)
    if body is None:
        return markdown
    blocks = _split_blocks(body)
    if not blocks:
        return markdown

    trailing = []
    cards = []
    for match, block_text in blocks:
        is_bad, number, iframe_html, caption = _parse_block(match, block_text)
        tag_match = _SOURCE_TAG_RE.search(caption)
        if tag_match:
            trailing.append(tag_match.group(1))
            caption = caption[: tag_match.start()].strip()
        cards.append(_render_card(is_bad, number, iframe_html, caption))

    grid_html = '<div class="example-grid">' + "".join(cards) + "</div>\n"
    if trailing:
        grid_html += "\n" + "\n".join(trailing) + "\n"

    heading_line = f"## {heading}"
    old_section = f"{heading_line}\n{body}"
    new_section = f"{heading_line}\n\n{grid_html}"
    return markdown.replace(old_section, new_section, 1)


def on_page_markdown(markdown, page, config, files):
    """Специфично для manual-2-etap/02-segments.md: блоки "**Пример N:** <iframe>...</iframe>" +
    картинка-кадр + подпись превращает в .example-grid/.example-card (карточка со встроенным
    плеером вместо статичного кадра — кадр становится избыточным, раз видео уже играбельно).
    Требует, чтобы embed_video_links.py уже отработал на этой странице раньше в конвейере хуков."""
    src_uri = page.file.src_uri.replace("\\", "/")
    if src_uri != TARGET_FILE:
        return markdown
    for heading in SECTION_HEADINGS:
        markdown = _transform_section(markdown, heading)
    return markdown

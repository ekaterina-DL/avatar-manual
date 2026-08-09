import re

from _list_utils import split_list_items

_HEADING_RE = re.compile(r'^(#{2,6})\s+(.*?)\s*$')
_ITEM_START_RE = re.compile(r'^-\s+')
_VIDEO_ITEM_RE = re.compile(
    r'^-\s*<video\b[^>]*><source\s+src="([^"]+)"\s+type="video/mp4">(.*?)</video>(.*)$',
    re.DOTALL,
)


def _flatten(item_text):
    return re.sub(r'\n\s*', ' ', item_text).strip()


def _parse_video_item(item_text):
    match = _VIDEO_ITEM_RE.match(_flatten(item_text))
    if not match:
        return None
    src, inner_caption, trailing = match.groups()
    caption = (inner_caption + trailing).strip()
    return src, caption


def _render_video_block(heading, items):
    cards = []
    for src, caption in items:
        cap_html = (
            f'<div class="vi-cap"><span markdown="1">{caption}</span></div>'
            if caption.strip(" .")
            else ""
        )
        cards.append(
            '<div class="video-item">'
            f'<video controls preload="metadata" src="{src}"></video>'
            f'{cap_html}'
            "</div>"
        )
    eyebrow = f'<span class="eyebrow">{heading}</span>' if heading else ""
    return (
        '<div class="video-block">'
        f'<div class="vb-head">{eyebrow}</div>'
        f'<div class="video-grid">{"".join(cards)}</div>'
        "</div>"
    )


def on_page_markdown(markdown, page, config, files):
    """Находит подряд идущие пункты списка (2 и более), каждый из которых — ровно один
    встроенный <video>, и оборачивает такую группу в .video-block/.video-grid. Одиночные
    видео-пункты и любые другие списки не трогает."""
    lines = markdown.split("\n")
    out_lines = []
    current_heading = ""
    i = 0
    n = len(lines)
    while i < n:
        heading_match = _HEADING_RE.match(lines[i])
        if heading_match:
            current_heading = heading_match.group(2)
            out_lines.append(lines[i])
            i += 1
            continue

        if _ITEM_START_RE.match(lines[i]):
            j = i
            while j < n and (lines[j].strip() != "" or j == i):
                if j > i and lines[j].strip() == "":
                    break
                j += 1
            list_lines = lines[i:j]
            items = split_list_items("\n".join(list_lines))
            parsed = [_parse_video_item(item) for item in items]
            if items and all(p is not None for p in parsed) and len(items) >= 2:
                out_lines.append(_render_video_block(current_heading, parsed))
            else:
                out_lines.extend(list_lines)
            i = j
            continue

        out_lines.append(lines[i])
        i += 1
    return "\n".join(out_lines)

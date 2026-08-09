import re

from _list_utils import split_list_items

_HEADING_RE = re.compile(r'^(#{2,6})\s+(.*?)\s*$')
_ITEM_START_RE = re.compile(r'^-\s+')
_VIDEO_TAG_RE = re.compile(
    r'<video\b[^>]*><source\s+src="([^"]+)"\s+type="video/mp4">(.*?)</video>',
    re.DOTALL,
)


def _flatten(item_text):
    return re.sub(r'\n\s*', ' ', item_text).strip()


def _clean_lead(text):
    """Готовит общую подпись пункта (текст перед первым видео) к использованию в карточке:
    снимает markdown-обёртку жирного текста ("**Быстрая речь:**" → "Быстрая речь") и висящее
    двоеточие/пробелы. Пустая строка, если перед видео вообще ничего не было (исходный, самый
    частый случай — пункт списка начинается сразу с видео)."""
    text = text.strip()
    match = re.match(r'^\*\*(.+?)\*\*:?$', text)
    if match:
        text = match.group(1)
    return text.strip(" :")


def _parse_video_item(item_text):
    """Разбирает один пункт списка на карточки (src, caption) — по одной на каждый <video>
    внутри пункта. Поддерживает два паттерна, оба реально встречаются в мануале:
    (1) пункт = один <video> сразу после "- ", подпись (если есть) идёт ПОСЛЕ тега — это
        исходный, самый частый случай (см. embed_local_media.py на голых .mp4-ссылках);
    (2) пункт = общая подпись ПЕРЕД одним или несколькими <video> подряд, например
        "- **Быстрая речь:** [пример 1](url1), [пример 2](url2)" (manual-2-etap/11-example-
        library.md, раздел "Темп речи") — раньше такой пункт не распознавался вообще (регулярка
        требовала, чтобы <video> шёл сразу после "- "), и весь список из-за этого оставался
        нераспакованным нагромождением полноразмерных плееров вместо компактной сетки.
    None, если в пункте нет ни одного видео (пункт не начинается с "- ", либо это не видео-пункт
    вовсе — тогда список групповать нельзя, см. on_page_markdown)."""
    flat = _flatten(item_text)
    start = _ITEM_START_RE.match(flat)
    if not start:
        return None
    body = flat[start.end():]
    videos = list(_VIDEO_TAG_RE.finditer(body))
    if not videos:
        return None
    lead = _clean_lead(body[:videos[0].start()])
    n = len(videos)
    parsed = []
    for i, m in enumerate(videos):
        src = m.group(1)
        inner_caption = m.group(2)
        # Текст между этим и следующим видео в том же пункте — как правило просто ", "
        # (разделитель перечисления примеров), в подпись карточки не идёт. Текст после
        # последнего видео — настоящая подпись-продолжение, как и в исходном (однo-видео)
        # случае, сохраняем буквально.
        trailing = body[m.end():] if i + 1 == n else ""
        own_caption = (inner_caption + trailing).strip()
        if lead and own_caption:
            caption = f"{lead} — {own_caption}"
        else:
            caption = own_caption or lead
        parsed.append((src, caption))
    return parsed


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
    """Находит подряд идущие пункты списка (2 и более), каждый из которых содержит один или
    несколько встроенных <video>, и оборачивает такую группу в .video-block/.video-grid. Пункт
    списка без единого <video> — сигнал, что это не список примеров, список не трогаем целиком."""
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
                # Один пункт списка может дать несколько карточек (несколько видео в одном
                # пункте, см. _parse_video_item) — разворачиваем в плоский список карточек.
                flat_cards = [pair for group in parsed for pair in group]
                out_lines.append(_render_video_block(current_heading, flat_cards))
            else:
                out_lines.extend(list_lines)
            i = j
            continue

        out_lines.append(lines[i])
        i += 1
    return "\n".join(out_lines)

import re

from _list_utils import split_list_items

_HEADING_RE = re.compile(r'^(#{2,6})\s+(.*?)\s*$')
_ITEM_START_RE = re.compile(r'^-\s+')
# Приватный сигнал от inject_example_previews.py: инжектированные превью полей классификатора
# вставляются посреди прозы целевой страницы без собственного markdown-заголовка, поэтому без
# этого маркера .video-block ниже унаследовал бы эйброу от ближайшего ПРЕДЫДУЩЕГО настоящего
# заголовка страницы (см. Concern 1 в отчёте Task 10) — а не название поля, которому превью
# реально посвящено. Строка вырезается из финального вывода, в HTML попасть не должна.
_EYEBROW_MARKER_RE = re.compile(r'^<!-- video-eyebrow: (.*) -->$')
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


def _render_list_block(current_heading, items):
    """items — список (raw_text, parsed) для ОДНОГО непрерывного markdown-списка (без пустых
    строк внутри). Не требует, чтобы список был однородным целиком: разбивает его на подряд
    идущие "прогоны" видео-пунктов и обычных пунктов, и группирует в .video-block только прогоны
    из 2+ видео-пунктов подряд — остальное (обычные пункты, картинки, одиночные видео-пункты)
    остаётся как есть, на своём месте в списке.

    Понадобилось из-за реального случая: manual-3-etap/07-example-library.md, раздел
    "Антипримеры" — 8 пунктов-видео подряд и ОДИН последний пункт-картинка
    (antiexample-8.jpg, сознательно оставлен картинкой, не видео — источник не скачан).
    Старая версия требовала однородности ВСЕГО списка (единый блок между пустыми строками) —
    из-за одной картинки в конце все 8 видео тоже оставались нераспакованным вертикальным
    стеком плееров на всю ширину, хотя сами по себе были бы валидным поводом для сетки."""
    runs = []
    for raw_text, parsed in items:
        is_video = parsed is not None
        if runs and runs[-1][0] == is_video:
            runs[-1][1].append((raw_text, parsed))
        else:
            runs.append((is_video, [(raw_text, parsed)]))

    rendered = []
    for is_video, run_items in runs:
        if is_video and len(run_items) >= 2:
            flat_cards = [pair for _, parsed in run_items for pair in parsed]
            rendered.append(_render_video_block(current_heading, flat_cards))
        else:
            rendered.append("\n".join(raw_text for raw_text, _ in run_items))
    return "\n".join(rendered)


def on_page_markdown(markdown, page, config, files):
    """Находит подряд идущие пункты списка, каждый из которых содержит один или несколько
    встроенных <video>, и оборачивает подряд идущие прогоны из 2+ таких пунктов в
    .video-block/.video-grid — не обязательно весь список целиком (см. _render_list_block:
    список из 8 видео + 1 картинки в конце всё равно даст 8-карточную сетку + отдельную
    картинку, а не полный отказ от группировки из-за одного несовпавшего пункта)."""
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

        eyebrow_match = _EYEBROW_MARKER_RE.match(lines[i])
        if eyebrow_match:
            current_heading = eyebrow_match.group(1)
            # Строка-маркер намеренно НЕ добавляется в out_lines — это приватный сигнал между
            # хуками, не контент, ему не место в собранном HTML.
            i += 1
            continue

        if _ITEM_START_RE.match(lines[i]):
            j = i
            while j < n and (lines[j].strip() != "" or j == i):
                if j > i and lines[j].strip() == "":
                    break
                j += 1
            list_lines = lines[i:j]
            items_text = split_list_items("\n".join(list_lines))
            items = [(text, _parse_video_item(text)) for text in items_text]
            if items:
                out_lines.append(_render_list_block(current_heading, items))
            else:
                out_lines.extend(list_lines)
            i = j
            continue

        out_lines.append(lines[i])
        i += 1
    return "\n".join(out_lines)

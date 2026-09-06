import re

from _list_utils import split_list_items
from _path_utils import fix_local_asset_path

_HEADING_RE = re.compile(r'^(#{2,6})\s+(.*?)\s*$')
_ITEM_START_RE = re.compile(r'^-\s+')
# Приватный сигнал от inject_example_previews.py: инжектированные превью полей классификатора
# вставляются посреди прозы целевой страницы без собственного markdown-заголовка, поэтому без
# этого маркера .video-block ниже унаследовал бы эйброу от ближайшего ПРЕДЫДУЩЕГО настоящего
# заголовка страницы (см. Concern 1 в отчёте Task 10) — а не название поля, которому превью
# реально посвящено. Строка вырезается из финального вывода, в HTML попасть не должна.
_EYEBROW_MARKER_RE = re.compile(r'^<!-- video-eyebrow: (.*) -->$')
# type="video/(?:mp4|webm)" — embed_local_media.py умеет оборачивать оба расширения (см. его
# _MIME_BY_EXT), а этот паттерн раньше был жёстко привязан к video/mp4: .webm-пункт списка
# незаметно не распознавался как медиа-пункт, разрывал прогон и выпадал из .video-grid как
# голый одиночный <li><video>...</video></li> — подпись при этом не исчезала, а просто уходила
# в fallback-содержимое <video> (невидимое в браузере), см. manual-2-etap/06-common-mistakes.md.
_VIDEO_TAG_RE = re.compile(
    r'<video\b[^>]*><source\s+src="([^"]+)"\s+type="video/(?:mp4|webm)">(.*?)</video>',
    re.DOTALL,
)
# Явный opt-in для картиночной карточки в сетке: "- ![grid: Подпись](путь)". Без префикса
# "grid: " картиночный пункт списка НЕ считается медиа-пунктом и в сетку не затягивается (см.
# _parse_media_item) — например, manual-3-etap/07-example-library.md держит antiexample-8.jpg
# как обычный пункт списка ПОСЛЕ прогона видео именно потому, что источник видео не скачан и
# картинка не должна маскироваться под полноценный пример-карточку (см. test_trailing_non_video_
# item_does_not_sink_whole_list). Префикс нужен ровно там, где картинка — намеренная замена
# видео-примера (например, скриншот вместо утраченного видео-источника).
_GRID_IMAGE_RE = re.compile(r'^!\[grid:\s*(.*?)\]\(([^)]+)\)$')
# "Подпись перед видео" (см. _parse_video_item, паттерн 2) — легитимна ТОЛЬКО когда весь текст
# перед первым видео в пункте это короткая жирная подпись вида "**Средний темп:**" и больше
# ничего (ни вступления до неё, ни хвоста после закрывающих "**" в пределах лида). Полная
# фраза-абзац, который просто СОДЕРЖИТ где-то ссылку на видео (обычный случай цитирования
# видео посреди рассуждения), под этот паттерн попадать не должна — см. Bug 5 в отчёте Task 10.
_STRICT_LABEL_LEAD_RE = re.compile(r'^\*\*[^*\n]+:\*\*$')
# Хвост ПОСЛЕ последнего видео при паттерне "подпись перед видео" — допускаем только пустоту
# или чисто пунктуационный хвост (пробелы/точки/тире/кавычки и т.п.), без единой буквы или
# цифры. Реальный корпус подтверждает: у легитимных случаев ("Темп речи") хвоста после видео
# нет вообще; у регрессий (10-qa-log.md, 03-common-mistakes.md) после видео всегда идёт ещё
# один полноценный кусок прозы (новое предложение, часто с собственным "**Ответ:**") — то есть
# наличие ЛЮБОГО буквенного символа в хвосте однозначно выдаёт "это не карточка-подпись".
_TRIVIAL_TRAILING_RE = re.compile(r'^[\s.,;:!?…\-–—"\'»\])]*$')


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
        Паттерн (2) распознаётся, ТОЛЬКО если весь текст перед первым видео — целиком короткая
        жирная подпись ("**Средний темп:**", см. _STRICT_LABEL_LEAD_RE) и после последнего видео
        в пункте нет содержательного текста (см. _TRIVIAL_TRAILING_RE). Иначе (полноразмерный
        абзац прозы, который просто где-то по ходу цитирует ссылку на видео) пункт НЕ считается
        видео-пунктом — см. Bug 5 в отчёте Task 10: manual-2-etap/10-qa-log.md ("вопросы команды
        к заказчику") и manual-3-etap/03-common-mistakes.md ("Калиброванные примеры") раньше
        ошибочно рвались на .video-block из-за того же самого поиска <video> "где угодно".
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
    raw_lead = body[:videos[0].start()].strip()
    if raw_lead:
        # Видео найдено НЕ сразу после "- " — легитимно только для паттерна 2 (короткая жирная
        # подпись перед видео, ничего больше в лиде) И только если после последнего видео в
        # пункте не осталось содержательного текста. Иначе это не "подпись + видео"-карточка, а
        # обычная проза, где ссылка на видео — просто одна из цитат посреди абзаца (Bug 5).
        if not _STRICT_LABEL_LEAD_RE.match(raw_lead):
            return None
        if not _TRIVIAL_TRAILING_RE.match(body[videos[-1].end():]):
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


def _parse_media_item(item_text):
    """Как _parse_video_item, но дополнительно распознаёт "grid-картинки" — пункты списка вида
    "- ![grid: Подпись](путь)" (см. _GRID_IMAGE_RE), которые должны попасть в ту же сетку
    .video-grid, что и соседние видео-карточки (тот же размер карточки, то же оформление).
    Без префикса "grid: " картиночный пункт медиа-пунктом не считается — обычные иллюстрации
    (например, antiexample-8.jpg) по умолчанию в сетку не затягиваются, см. комментарий у
    _GRID_IMAGE_RE. Возвращает список ("video"|"image", src, caption) — None, если пункт не
    является ни видео-, ни grid-картиночным."""
    video_cards = _parse_video_item(item_text)
    if video_cards is not None:
        return [("video", src, caption) for src, caption in video_cards]
    flat = _flatten(item_text)
    start = _ITEM_START_RE.match(flat)
    if not start:
        return None
    body = flat[start.end():].strip()
    match = _GRID_IMAGE_RE.match(body)
    if not match:
        return None
    caption, src = match.group(1).strip(), match.group(2)
    return [("image", src, caption)]


def _render_video_block(heading, items):
    """markdown="1" должен стоять на КАЖДОМ вложенном <div>-предке подписи (video-block,
    video-grid, video-item, vi-cap), а сама подпись — на отдельной строке, а не в одной строке
    со всеми окружающими тегами. Иначе md_in_html не перерабатывает markdown внутри подписи —
    см. Fix 1 итогового обзора. Подписи здесь всегда однострочные (собраны через _flatten в
    _parse_video_item), поэтому, в отличие от build_segment_examples.py, пустая строка перед
    списком не нужна — списков в подписи не бывает."""
    cards = []
    for kind, src, caption in items:
        if kind == "video":
            media_tag = f'<video controls preload="metadata" src="{src}"></video>'
        else:
            alt = caption.replace('"', "&quot;")
            media_tag = f'<img alt="{alt}" src="{fix_local_asset_path(src)}" loading="lazy">'
        if caption.strip(" ."):
            card = (
                '<div class="video-item" markdown="1">\n'
                f'{media_tag}\n'
                '<div class="vi-cap" markdown="1">\n'
                f'{caption}\n'
                "</div>\n"
                "</div>"
            )
        else:
            card = (
                '<div class="video-item">'
                f'{media_tag}'
                "</div>"
            )
        cards.append(card)
    eyebrow = f'<span class="eyebrow">{heading}</span>' if heading else ""
    return (
        '<div class="video-block" markdown="1">\n'
        f'<div class="vb-head">{eyebrow}</div>\n'
        '<div class="video-grid" markdown="1">\n'
        + "\n".join(cards) +
        "\n</div>\n"
        "</div>"
    )


def _render_list_block(current_heading, items):
    """items — список (raw_text, parsed) для ОДНОГО непрерывного markdown-списка (без пустых
    строк внутри). Не требует, чтобы список был однородным целиком: разбивает его на подряд
    идущие "прогоны" медиа-пунктов (видео и явных grid-картинок, см. _parse_media_item) и
    обычных пунктов, и группирует в .video-block любой прогон медиа-пунктов (даже из 1) —
    остальное (обычные пункты, не-grid картинки) остаётся как есть, на своём месте в списке.

    Понадобилось из-за реального случая: manual-3-etap/07-example-library.md, раздел
    "Антипримеры" — 8 пунктов-видео подряд и ОДИН последний пункт-картинка
    (antiexample-8.jpg, сознательно оставлен картинкой, не видео — источник не скачан).
    Старая версия требовала однородности ВСЕГО списка (единый блок между пустыми строками) —
    из-за одной картинки в конце все 8 видео тоже оставались нераспакованным вертикальным
    стеком плееров на всю ширину, хотя сами по себе были бы валидным поводом для сетки.

    Прогоны из 1 медиа-пункта тоже оборачиваются в .video-block (сетка из одной карточки), а не
    только 2+ — раньше одиночное видео проваливалось в голый <li><video>...</video></li>: подпись
    уходила в невидимое fallback-содержимое <video>, а маркер списка "•" не скрывался, т.к. видео
    не было завёрнуто в .video-item. Всплыло 06.09.2026 на manual-2-etap/11-example-library.md,
    раздел "Артефакт" — после чистки раздела (см. журнал) от 5 видео осталось только 1."""
    runs = []
    for raw_text, parsed in items:
        is_media = parsed is not None
        if runs and runs[-1][0] == is_media:
            runs[-1][1].append((raw_text, parsed))
        else:
            runs.append((is_media, [(raw_text, parsed)]))

    rendered = []
    for is_media, run_items in runs:
        if is_media:
            flat_cards = [triple for _, parsed in run_items for triple in parsed]
            rendered.append(_render_video_block(current_heading, flat_cards))
        else:
            rendered.append("\n".join(raw_text for raw_text, _ in run_items))
    return "\n".join(rendered)


def on_page_markdown(markdown, page, config, files):
    """Находит подряд идущие пункты списка, каждый из которых содержит один или несколько
    встроенных <video>, и оборачивает подряд идущие прогоны таких пунктов (даже прогон из 1) в
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
            items = [(text, _parse_media_item(text)) for text in items_text]
            if items:
                out_lines.append(_render_list_block(current_heading, items))
            else:
                out_lines.extend(list_lines)
            i = j
            continue

        out_lines.append(lines[i])
        i += 1
    return "\n".join(out_lines)

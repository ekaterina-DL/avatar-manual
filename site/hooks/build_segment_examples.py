import re

from _build_profile import is_pdf_build
from _section_utils import extract_section

TARGET_FILES = {
    "manual-2-etap/05-what-to-label.md",
    "manual-2-etap/05b-what-not-to-label.md",
}
SECTION_HEADINGS = ["Примеры (позитивные)", "Антипримеры"]

# Строка списка (маркированная "- " или нумерованная "1. ") внутри подписи карточки. Нужна
# для _prepare_caption_block: markdown (в т.ч. md_in_html) распознаёт список только если перед
# ним есть пустая строка — без неё строки списка сливаются в один run-on абзац с предыдущим
# текстом (см. Fix 1 итогового обзора, Пример 2 и Антипример 1).
_LIST_ITEM_RE = re.compile(r'^(?:[-*]\s+|\d+\.\s+)')
# Строка-продолжение предыдущего пункта списка (перенос длинной строки с отступом, выравненным
# под маркер) — например, "   человеком длительностью более 10 сек." в Антипримере 1 реального
# 02-segments.md. ВАЖНО отличать от новой строки списка/абзаца: если считать такую строку
# "не-списком" наравне с настоящим абзацем после списка, вставленная перед ней пустая строка
# рвёт список на несколько отдельных <ol> с "выпавшими" продолжениями пунктов в виде отдельных
# <p> — реальная регрессия, найденная на живой собранной странице при проверке этого фикса.
_LIST_CONTINUATION_RE = re.compile(r'^\s+\S')

_BLOCK_START_RE = re.compile(
    r'\*\*((?:Анти)?[Пп]ример) (\d+):\*\*[ \t]*(<iframe.*?</iframe>)[ \t]*\n'
)
_IMAGE_LINE_RE = re.compile(r'!\[[^\]]*\]\([^)]+\)\n?')
_SOURCE_TAG_RE = re.compile(
    r'\n((?:`\[[^`\n]*\]`)|(?:<span class="source-tag">\[[^\n]*?\]</span>))\s*$'
)


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


def _prepare_caption_block(caption):
    """Вставляет пустую строку перед первой строкой списка на границе список/не-список (в обе
    стороны), если её там ещё нет — иначе md_in_html не распознаёт список как отдельный блок и
    схлопывает его в один run-on абзац с предыдущим текстом (баг из итогового обзора, Fix 1:
    Пример 2 — вложенный список; Антипример 1 — нумерованный список). Строки-продолжения пункта
    (с отступом, без своего маркера) НЕ считаются переходом список/не-список — иначе список
    рвётся на несколько отдельных <ol>/<ul> с продолжениями пунктов, утёкшими в отдельные <p>
    (реальная регрессия, найденная на живой собранной странице)."""
    lines = caption.split("\n")
    out = []
    in_list = False
    for line in lines:
        if not line.strip():
            out.append(line)
            continue
        is_item_start = bool(_LIST_ITEM_RE.match(line))
        is_continuation = not is_item_start and bool(_LIST_CONTINUATION_RE.match(line))
        if not is_continuation:
            is_list_line = is_item_start
            if out and out[-1].strip() and is_list_line != in_list:
                out.append("")
            in_list = is_list_line
        out.append(line)
    return "\n".join(out)


def _render_card(is_bad, number, iframe_html, caption):
    """markdown="1" должен стоять на КАЖДОМ вложенном <div>-предке подписи (а не только на
    внутреннем контейнере), а сама подпись — на отдельной строке(-ах), с пустой строкой перед
    любым блочным содержимым (списки). Иначе MkDocs'ный md_in_html не перерабатывает markdown
    внутри блока — см. Fix 1 итогового обзора: **bold** и списки утекали в вывод буквально."""
    card_class = "example-card bad" if is_bad else "example-card"
    caption_block = _prepare_caption_block(caption)
    return (
        f'<div class="{card_class}" markdown="1">\n'
        f'{iframe_html}\n'
        '<div class="ec-body" markdown="1">\n'
        f'<span class="num">{number}</span>\n'
        "\n"
        f'{caption_block}\n'
        "\n"
        "</div>\n"
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

    grid_html = '<div class="example-grid" markdown="1">\n' + "\n".join(cards) + "\n</div>\n"
    if trailing:
        grid_html += "\n" + "\n".join(trailing) + "\n"

    heading_line = f"## {heading}"
    old_section = f"{heading_line}\n{body}"
    new_section = f"{heading_line}\n\n{grid_html}"
    return markdown.replace(old_section, new_section, 1)


def on_page_markdown(markdown, page, config, files):
    """Специфично для manual-2-etap/05-what-to-label.md и manual-2-etap/05b-what-not-to-label.md:
    блоки "**Пример N:** <iframe>...</iframe>" + картинка-кадр + подпись превращает в
    .example-grid/.example-card (карточка со встроенным плеером вместо статичного кадра — кадр
    становится избыточным, раз видео уже играбельно). Разделы «Примеры (позитивные)» и
    «Антипримеры» изначально жили вместе на 02-segments.md, но постепенно оба переехали:
    «Антипримеры» — на 05b-what-not-to-label.md, «Примеры (позитивные)» — на 05-what-to-label.md.
    Хук проверяет оба целевых файла на оба заголовка — extract_section просто не находит
    отсутствующий заголовок и no-op'ает для него, так что каждый файл фактически обрабатывает
    только тот раздел, который у него есть. Требует, чтобы embed_video_links.py уже отработал на
    странице раньше в конвейере хуков.

    PDF-профиль — исключение (Fix 3 итогового обзора, человек решил): карточка со встроенным
    плеером в печати бесполезна (iframe нельзя кликнуть, постер не показывается), из-за чего
    PDF-читатель видел пустые боксы без единого способа опознать видео. Раз embed_video_links.py
    теперь no-op на PDF-профиле (там просто нет <iframe> для сборки карточки), этот hook тоже
    no-op — восстанавливает досайтовое поведение (кадр-картинка + подпись + кликабельная ссылка
    как обычный markdown)."""
    if is_pdf_build(config):
        return markdown
    src_uri = page.file.src_uri.replace("\\", "/")
    if src_uri not in TARGET_FILES:
        return markdown
    for heading in SECTION_HEADINGS:
        markdown = _transform_section(markdown, heading)
    return markdown

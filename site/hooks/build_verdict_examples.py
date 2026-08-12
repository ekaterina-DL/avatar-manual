import re

from _build_profile import is_pdf_build

TARGET_FILE = "manual-3-etap/03-common-mistakes.md"

_HEADER_RE = re.compile(
    r'\| Вердикт заказчика \| Признак \| Пример \|\n'
    r'\|[-: ]+\|[-: ]+\|[-: ]+\|\n'
)
_ROW_RE = re.compile(
    r'\| (Битое|Подходящее видео|Артефакт \(не битое\)) \| (.+) \| (.+) \|'
)

_CARD_CLASS = {
    "Битое": "bad",
    "Подходящее видео": "good",
    "Артефакт (не битое)": "warn",
}

_VERDICT_TAG = {
    "Битое": "🚫 Битое",
    "Подходящее видео": "✅ Подходящее",
    "Артефакт (не битое)": "🟡 Артефакт",
}


def _render_card(verdict, feature, video_html):
    card_class = f"example-card {_CARD_CLASS[verdict]}"
    tag = _VERDICT_TAG[verdict]
    return (
        f'<div class="{card_class}" markdown="1">\n'
        f'{video_html}\n'
        '<div class="ec-body" markdown="1">\n'
        f'<span class="ec-verdict">{tag}</span>\n'
        "\n"
        f'{feature}\n'
        "\n"
        "</div>\n"
        "</div>"
    )


def _transform(markdown):
    header_match = _HEADER_RE.search(markdown)
    if not header_match:
        return markdown
    rest = markdown[header_match.end():]
    cards = []
    consumed = 0
    for line in rest.splitlines(keepends=True):
        row_match = _ROW_RE.fullmatch(line.strip())
        if not row_match:
            break
        verdict, feature, video_html = row_match.groups()
        cards.append(_render_card(verdict, feature.strip(), video_html.strip()))
        consumed += len(line)
    if not cards:
        return markdown
    table_text = markdown[header_match.start():header_match.end() + consumed]
    grid_html = '<div class="example-grid" markdown="1">\n' + "\n".join(cards) + "\n</div>"
    return markdown.replace(table_text, grid_html, 1)


def on_page_markdown(markdown, page, config, files):
    """Таблица "| Вердикт заказчика | Признак | Пример |" в manual-3-etap/03-common-mistakes.md
    (раздел "Битое или артефакт калибровка по пикселизации и цвету", 18 строк) превращается в
    .example-grid/.example-card с цветным тегом-вердиктом вместо голой ссылки на видео в ячейке.
    Матчит таблицу по заголовку колонок (устойчиво к правкам окружающей прозы — тот же принцип,
    что в build_compare_cards.py), а не по всему разделу целиком, поэтому вступительный и
    заключительный абзацы раздела остаются нетронутыми текстом снаружи новой сетки. Должен
    выполняться после hooks/embed_local_media.py — в колонке "Пример" на входе уже готовый
    <video>-тег, а не голая ссылка на .mp4. PDF-профиль — no-op (тот же принцип, что в
    build_segment_examples.py): в печати таблица остаётся обычной, а ссылка на видео уже
    кликабельна как текст через embed_local_media.py (эта часть не зависит от профиля)."""
    if is_pdf_build(config):
        return markdown
    src_uri = page.file.src_uri.replace("\\", "/")
    if src_uri != TARGET_FILE:
        return markdown
    return _transform(markdown)

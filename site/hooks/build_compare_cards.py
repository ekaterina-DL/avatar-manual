import re

_TABLE_RE = re.compile(
    r'\|\s*Правильно\s*\|\s*Неправильно\s*\|\n'
    r'\|[-: ]+\|[-: ]+\|\n'
    r'\|\s*!\[([^\]]*)\]\(([^)]+)\)\s*\|\s*!\[([^\]]*)\]\(([^)]+)\)\s*\|\n'
    r'\|\s*([^|\n]*?)\s*\|\s*([^|\n]*?)\s*\|'
)


def _render(match):
    alt_good, src_good, alt_bad, src_bad, cap_good, cap_bad = match.groups()
    return (
        '<div class="compare">'
        '<div class="compare-card good">'
        f'<img src="{src_good}" alt="{alt_good}">'
        '<div class="compare-tag">✓ Правильно</div>'
        f'<div class="compare-cap"><span markdown="1">{cap_good}</span></div>'
        '</div>'
        '<div class="compare-card bad">'
        f'<img src="{src_bad}" alt="{alt_bad}">'
        '<div class="compare-tag">✗ Неправильно</div>'
        f'<div class="compare-cap"><span markdown="1">{cap_bad}</span></div>'
        '</div>'
        '</div>'
    )


def on_page_markdown(markdown, page, config, files):
    """Двухколоночная таблица с заголовками ровно "Правильно"/"Неправильно", где в первой
    строке данных — картинки, а во второй — подписи, превращается в .compare/.compare-card
    (картинка с zoom по наведению, цветная плашка, подпись). Таблицы без картинок или с другими
    заголовками не трогает."""
    return _TABLE_RE.sub(_render, markdown)

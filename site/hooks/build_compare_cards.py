import re

from _path_utils import fix_local_asset_path

_TABLE_RE = re.compile(
    r'\|\s*Правильно\s*\|\s*Неправильно\s*\|\n'
    r'\|[-: ]+\|[-: ]+\|\n'
    r'\|\s*!\[([^\]]*)\]\(([^)]+)\)\s*\|\s*!\[([^\]]*)\]\(([^)]+)\)\s*\|\n'
    r'\|\s*([^|\n]*?)\s*\|\s*([^|\n]*?)\s*\|'
)


def _render(match):
    """markdown="1" должен стоять на КАЖДОМ вложенном <div>-предке подписи (.compare,
    .compare-card, .compare-cap), а сама подпись — на отдельной строке. Иначе md_in_html не
    перерабатывает markdown внутри подписи — см. Fix 1 итогового обзора. Побочный эффект: img
    (span-level тег в терминах markdown.util.BLOCK_LEVEL_ELEMENTS, в отличие от iframe/video)
    внутри markdown="1"-блока тоже оборачивается в <p> — нейтрализовано в extra.css
    (".compare-card p { margin: 0; }"), чтобы не появился лишний отступ под картинкой/подписью."""
    alt_good, src_good, alt_bad, src_bad, cap_good, cap_bad = match.groups()
    src_good = fix_local_asset_path(src_good)
    src_bad = fix_local_asset_path(src_bad)
    return (
        '<div class="compare" markdown="1">\n'
        '<div class="compare-card good" markdown="1">\n'
        f'<img src="{src_good}" alt="{alt_good}">\n'
        '<div class="compare-tag">✓ Правильно</div>\n'
        '<div class="compare-cap" markdown="1">\n'
        f'{cap_good}\n'
        "</div>\n"
        "</div>\n"
        '<div class="compare-card bad" markdown="1">\n'
        f'<img src="{src_bad}" alt="{alt_bad}">\n'
        '<div class="compare-tag">✗ Неправильно</div>\n'
        '<div class="compare-cap" markdown="1">\n'
        f'{cap_bad}\n'
        "</div>\n"
        "</div>\n"
        "</div>"
    )


def on_page_markdown(markdown, page, config, files):
    """Двухколоночная таблица с заголовками ровно "Правильно"/"Неправильно", где в первой
    строке данных — картинки, а во второй — подписи, превращается в .compare/.compare-card
    (картинка с zoom по наведению, цветная плашка, подпись). Таблицы без картинок или с другими
    заголовками не трогает."""
    return _TABLE_RE.sub(_render, markdown)

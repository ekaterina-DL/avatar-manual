from build_segment_examples import on_page_markdown
from _render_helpers import render_html

IFRAME_1 = '<iframe class="embedded-video" src="https://vk.com/video_ext.php?oid=1&id=1&hd=2" loading="lazy" allowfullscreen></iframe>'
IFRAME_2 = '<iframe class="embedded-video" src="https://vk.com/video_ext.php?oid=2&id=2&hd=2" loading="lazy" allowfullscreen></iframe>'
IFRAME_3 = '<iframe class="embedded-video" src="https://vk.com/video_ext.php?oid=3&id=3&hd=2" loading="lazy" allowfullscreen></iframe>'
# Вид тега, который embed_local_media.py ставит на месте локальной .mp4/.webm ссылки — карточка
# должна опознавать и его, не только <iframe> (см. запись 02.09.2026 в _BLOCK_START_RE).
VIDEO_1 = '<video controls preload="metadata" style="max-width:100%"><source src="assets/pamela.mp4" type="video/mp4"></video>'

SEGMENTS_MD = f"""## Примеры (позитивные)

**Пример 1:** {IFRAME_1}
![Пример 1: женщина на нейтральном тёмном фоне, говорит](assets/example1-frame.jpeg)
Отрывок с речью. Можно выделить сегмент от 10 сек.
**Подходящий сегмент: 0:02 – 02:57.**

**Пример 2:** {IFRAME_2}
![Пример 2: девушка поёт у пианино](assets/example2-frame.jpeg)
Отрывок с пением.
**Подходящие сегменты:**
- сегмент с плечами: 0:08 – 0:37
- сегмент с появлением рук: 0:37 – 02:40

`[Инстр. Kandinsky-Аватар, стр.5-7]`

## Антипримеры

**Антипример 1:** {IFRAME_3}
![Антипример 1: вертикальное видео](assets/antiexample1-frame.jpeg)
1. Не должно быть сопроводительных текстов на видео.
2. В видео должна быть хотя бы одна непрерывная сцена.

`[Инстр. Kandinsky-Аватар, стр.7-10]`
"""


class FakeFile:
    src_uri = "manual-2-etap/05-what-to-label.md"


class FakePage:
    file = FakeFile()


class FakeSiteDir:
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return self._value


class FakeConfig(dict):
    def __init__(self, site_dir):
        super().__init__()
        self.site_dir = FakeSiteDir(site_dir)


# Хук теперь читает config.site_dir (Fix 3 итогового обзора: no-op на PDF-профиле) — все
# существующие тесты сайта используют не-PDF site_dir, чтобы явно проверять поведение САЙТА.
SITE_CONFIG = FakeConfig("/repo/avatar-manual-build/build")
PDF_CONFIG = FakeConfig("/repo/avatar-manual-build/build-pdf")


def test_builds_two_grids_positive_and_negative():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), SITE_CONFIG, None)
    assert result.count('<div class="example-grid" markdown="1">') == 2
    assert result.count('<div class="example-card" markdown="1">') == 2  # два положительных
    assert result.count('<div class="example-card bad" markdown="1">') == 1  # один антипример


def test_card_contains_iframe_not_static_image():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), SITE_CONFIG, None)
    assert IFRAME_1 in result
    assert 'src="assets/example1-frame.jpeg"' not in result


def test_card_preserves_full_caption_including_nested_list():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), SITE_CONFIG, None)
    assert "сегмент с появлением рук: 0:37 – 02:40" in result
    assert "Подходящие сегменты" in result


def test_card_preserves_numbered_caption():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), SITE_CONFIG, None)
    assert "непрерывная сцена" in result


def test_source_tag_kept_outside_cards():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), SITE_CONFIG, None)
    assert "[Инстр. Kandinsky-Аватар, стр.5-7]" in result
    assert "[Инстр. Kandinsky-Аватар, стр.7-10]" in result


def test_card_recognizes_local_video_tag_not_only_iframe():
    """embed_local_media.py оборачивает локальные .mp4/.webm в <video>, а не <iframe> — карточка
    должна опознавать и такой пример как полноценный "Пример N", а не проглатывать его в подпись
    предыдущей карточки (тот самый баг с не-iframe контентом внутри этих двух разделов)."""
    md = f"""## Примеры (позитивные)

**Пример 1:** {IFRAME_1}
![Пример 1: женщина на нейтральном тёмном фоне, говорит](assets/example1-frame.jpeg)
Отрывок с речью.

**Пример 2:** {VIDEO_1}
![Пример 2: локальное видео](assets/pamela-frame.jpeg)
Локальный файл вместо заблокированной VK-ссылки.
"""
    result = on_page_markdown(md, FakePage(), SITE_CONFIG, None)
    assert result.count('<div class="example-card" markdown="1">') == 2
    assert VIDEO_1 in result
    assert "Отрывок с речью." in result
    assert "Локальный файл вместо заблокированной VK-ссылки." in result
    # подпись первой карточки не должна была "проглотить" вторую
    assert "Отрывок с речью.\nЛокальный файл" not in result


def test_untouched_on_other_pages():
    class OtherFile:
        src_uri = "manual-2-etap/04-classifier.md"

    class OtherPage:
        file = OtherFile()

    assert on_page_markdown(SEGMENTS_MD, OtherPage(), SITE_CONFIG, None) == SEGMENTS_MD


def test_untouched_on_segments_page():
    """«Примеры (позитивные)» и «Антипримеры» изначально жили вместе на 02-segments.md, но оба
    раздела переехали (сначала «Антипримеры» на 05b-what-not-to-label.md, затем «Примеры
    (позитивные)» на 05-what-to-label.md) — 02-segments.md больше не должен быть целью хука."""
    class SegmentsFile:
        src_uri = "manual-2-etap/02-segments.md"

    class SegmentsPage:
        file = SegmentsFile()

    assert on_page_markdown(SEGMENTS_MD, SegmentsPage(), SITE_CONFIG, None) == SEGMENTS_MD


def test_also_runs_on_what_not_to_label_page():
    """«Примеры (позитивные)» и «Антипримеры» теперь живут на разных страницах
    (05-what-to-label.md и 05b-what-not-to-label.md соответственно) — хук должен собирать
    карточки на обеих, а не только на одной TARGET_FILE из старой (одиночной) версии."""
    class WhatNotFile:
        src_uri = "manual-2-etap/05b-what-not-to-label.md"

    class WhatNotPage:
        file = WhatNotFile()

    result = on_page_markdown(SEGMENTS_MD, WhatNotPage(), SITE_CONFIG, None)
    assert result.count('<div class="example-grid" markdown="1">') == 2


def test_rendered_html_has_no_leftover_markdown_1_or_literal_bold_markers():
    """Fix 1 итогового обзора: markdown="1" стоял только на самом внутреннем <div>, а не на
    ВСЕХ div-предках карточки, и подпись шла в одну строку с окружающими тегами — из-за этого
    markdown="1" был мёртвым атрибутом: **bold** и списки утекали в собранную страницу буквально
    (подтверждено на живой собранной странице manual-2-etap/02-segments.md). Проверяем через
    настоящий рендер markdown.markdown() (см. tests/_render_helpers.py), а не промежуточную
    строку хука — она бы не показала, реально ли отработал markdown="1"."""
    result = on_page_markdown(SEGMENTS_MD, FakePage(), SITE_CONFIG, None)
    html = render_html(result)
    assert 'markdown="1"' not in html
    assert "**" not in html


def test_rendered_html_example2_nested_list_becomes_real_ul():
    """Пример 2: подпись "**Подходящие сегменты:**" + вложенный список (два пункта) должна
    рендериться как настоящий <ul><li>, а не схлопываться в один run-on абзац (баг из
    итогового обзора)."""
    result = on_page_markdown(SEGMENTS_MD, FakePage(), SITE_CONFIG, None)
    html = render_html(result)
    assert "<ul>" in html
    assert "<li>сегмент с плечами: 0:08 – 0:37</li>" in html
    assert "<li>сегмент с появлением рук: 0:37 – 02:40</li>" in html
    assert "<strong>Подходящие сегменты:</strong>" in html


def test_rendered_html_antiexample1_numbered_list_becomes_real_ol():
    """Антипример 1: нумерованный список (1. 2.) должен рендериться как настоящий <ol><li>,
    а не схлопываться в один абзац (баг из итогового обзора)."""
    result = on_page_markdown(SEGMENTS_MD, FakePage(), SITE_CONFIG, None)
    html = render_html(result)
    assert "<ol>" in html
    assert "<li>Не должно быть сопроводительных текстов на видео.</li>" in html
    assert "<li>В видео должна быть хотя бы одна непрерывная сцена.</li>" in html


def test_rendered_html_example1_bold_caption_becomes_strong():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), SITE_CONFIG, None)
    html = render_html(result)
    assert "<strong>Подходящий сегмент: 0:02 – 02:57.</strong>" in html


def test_noop_on_pdf_build():
    """Fix 3 итогового обзора (человек решил): на PDF-профиле хук — полный no-op. В печати
    карточка со встроенным плеером бесполезна (iframe нельзя кликнуть, постер не показывается) —
    восстанавливаем досайтовое поведение (кадр-картинка + подпись как обычный markdown, а не
    .example-grid). Раз embed_video_links.py тоже no-op на PDF, в реальном PDF-конвейере на
    входе этого хука вообще не будет <iframe> — здесь же, с уже вставленным IFRAME_1/2/3,
    проверяем именно то, что этот хук САМ ПО СЕБЕ ничего не трогает на PDF-профиле."""
    result = on_page_markdown(SEGMENTS_MD, FakePage(), PDF_CONFIG, None)
    assert result == SEGMENTS_MD
    assert "example-grid" not in result


REAL_ANTIEXAMPLE1_MD = f"""## Антипримеры

**Антипример 1:** {IFRAME_3}
![Антипример 1: вертикальное видео с headphones, внизу наложен текст-субтитр](assets/antiexample1-frame.jpeg)
1. Не должно быть сопроводительных текстов на видео (субтитров).
2. В видео должна быть хотя бы одна непрерывная сцена (без резкой смены ракурса) с говорящим
   человеком длительностью более 10 сек.
3. В сцене не должно быть «перебивок» и «рывков» — когда при монтаже (обычно для сокращения)
   соединено несколько нарезанных фрагментов одного человека в одной и той же сцене в разные
   близкие моменты времени (пример — на 23–24 сек этого видео). Сцены должны быть плавными и
   естественными, без купюр.

`[Инстр. Kandinsky-Аватар, стр.7-10]`
"""


def test_rendered_html_numbered_list_with_wrapped_continuation_lines_stays_one_ol():
    """Регрессия, найденная на живой собранной странице manual-2-etap/02-segments.md при
    проверке этого фикса: реальный текст Антипримера 1 переносит пункты 2 и 3 на вторую строку
    с отступом в 3 пробела (markdown-синтаксис "продолжение пункта списка"), а не помещает весь
    пункт в одну строку, как в упрощённом фикстурном SEGMENTS_MD выше. Первая версия
    _prepare_caption_block считала такую строку-продолжение переходом список/не-список и
    вставляла перед ней пустую строку — список разваливался на несколько отдельных <ol> с
    "выпавшими" продолжениями пунктов в виде отдельных <p> (визуально сломанная нумерация)."""
    result = on_page_markdown(REAL_ANTIEXAMPLE1_MD, FakePage(), SITE_CONFIG, None)
    html = render_html(result)
    assert html.count("<ol>") == 1
    assert html.count("</ol>") == 1
    assert (
        "<li>В видео должна быть хотя бы одна непрерывная сцена (без резкой смены ракурса) "
        "с говорящим\n   человеком длительностью более 10 сек.</li>"
    ) in html
    assert (
        "<li>В сцене не должно быть «перебивок» и «рывков» — когда при монтаже (обычно для "
        "сокращения)\n   соединено несколько нарезанных фрагментов одного человека в одной и "
        "той же сцене в разные\n   близкие моменты времени (пример — на 23–24 сек этого видео). "
        "Сцены должны быть плавными и\n   естественными, без купюр.</li>"
    ) in html
    # ни одна строка-продолжение не "выпала" в отдельный <p> вне списка
    assert "<p>человеком длительностью" not in html
    assert "<p>соединено несколько" not in html


def test_span_wrapped_source_tag_kept_outside_cards():
    """В реальном конвейере hooks/wrap_source_tags.py отрабатывает РАНЬШЕ этого хука (см.
    site/mkdocs.yml) и уже успевает обернуть `[...]` в <span class="source-tag">[...]</span>
    до того, как build_segment_examples его увидит. Тег всё равно должен остаться отдельным
    абзацем СНАРУЖИ .example-grid, а не быть проглоченным в подпись последней карточки."""
    span_md = SEGMENTS_MD.replace(
        "`[Инстр. Kandinsky-Аватар, стр.5-7]`",
        '<span class="source-tag">[Инстр. Kandinsky-Аватар, стр.5-7]</span>',
    ).replace(
        "`[Инстр. Kandinsky-Аватар, стр.7-10]`",
        '<span class="source-tag">[Инстр. Kandinsky-Аватар, стр.7-10]</span>',
    )
    result = on_page_markdown(span_md, FakePage(), SITE_CONFIG, None)

    assert '<span class="source-tag">[Инстр. Kandinsky-Аватар, стр.5-7]</span>' in result
    assert '<span class="source-tag">[Инстр. Kandinsky-Аватар, стр.7-10]</span>' in result

    # Обе карточные сетки закрываются тремя подряд </div> (ec-body, card, grid), каждый на
    # своей строке (нужно для md_in_html, см. Fix 1 итогового обзора) — тег должен идти сразу
    # ПОСЛЕ этой последовательности отдельным абзацем, а не оказаться замешан внутрь последней
    # карточки (что и было багом со старой регуляркой, рассчитанной только на форму с обратными
    # кавычками).
    assert (
        '</div>\n</div>\n</div>\n\n'
        '<span class="source-tag">[Инстр. Kandinsky-Аватар, стр.5-7]</span>'
    ) in result
    assert (
        '</div>\n</div>\n</div>\n\n'
        '<span class="source-tag">[Инстр. Kandinsky-Аватар, стр.7-10]</span>'
    ) in result

from build_segment_examples import on_page_markdown

IFRAME_1 = '<iframe class="embedded-video" src="https://vk.com/video_ext.php?oid=1&id=1&hd=2" loading="lazy" allowfullscreen></iframe>'
IFRAME_2 = '<iframe class="embedded-video" src="https://vk.com/video_ext.php?oid=2&id=2&hd=2" loading="lazy" allowfullscreen></iframe>'
IFRAME_3 = '<iframe class="embedded-video" src="https://vk.com/video_ext.php?oid=3&id=3&hd=2" loading="lazy" allowfullscreen></iframe>'

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
    src_uri = "manual-2-etap/02-segments.md"


class FakePage:
    file = FakeFile()


def test_builds_two_grids_positive_and_negative():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), None, None)
    assert result.count('<div class="example-grid">') == 2
    assert result.count('<div class="example-card">') == 2  # два положительных
    assert result.count('<div class="example-card bad">') == 1  # один антипример


def test_card_contains_iframe_not_static_image():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), None, None)
    assert IFRAME_1 in result
    assert 'src="assets/example1-frame.jpeg"' not in result


def test_card_preserves_full_caption_including_nested_list():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), None, None)
    assert "сегмент с появлением рук: 0:37 – 02:40" in result
    assert "Подходящие сегменты" in result


def test_card_preserves_numbered_caption():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), None, None)
    assert "непрерывная сцена" in result


def test_source_tag_kept_outside_cards():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), None, None)
    assert "[Инстр. Kandinsky-Аватар, стр.5-7]" in result
    assert "[Инстр. Kandinsky-Аватар, стр.7-10]" in result


def test_untouched_on_other_pages():
    class OtherFile:
        src_uri = "manual-2-etap/04-classifier.md"

    class OtherPage:
        file = OtherFile()

    assert on_page_markdown(SEGMENTS_MD, OtherPage(), None, None) == SEGMENTS_MD


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
    result = on_page_markdown(span_md, FakePage(), None, None)

    assert '<span class="source-tag">[Инстр. Kandinsky-Аватар, стр.5-7]</span>' in result
    assert '<span class="source-tag">[Инстр. Kandinsky-Аватар, стр.7-10]</span>' in result

    # Обе карточные сетки закрываются четырьмя подряд </div> (markdown-div, ec-body,
    # card, grid) — тег должен идти сразу ПОСЛЕ этой последовательности отдельным абзацем,
    # а не оказаться замешан внутрь последней карточки (что и было багом со старой регуляркой,
    # рассчитанной только на форму с обратными кавычками).
    assert (
        '</div></div></div></div>\n\n'
        '<span class="source-tag">[Инстр. Kandinsky-Аватар, стр.5-7]</span>'
    ) in result
    assert (
        '</div></div></div></div>\n\n'
        '<span class="source-tag">[Инстр. Kandinsky-Аватар, стр.7-10]</span>'
    ) in result

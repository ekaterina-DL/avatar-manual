from group_media_lists import on_page_markdown


def test_groups_two_consecutive_video_items():
    md = (
        '## Примеры «Битое» (для калибровки, что считается явным браком)\n\n'
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/a.mp4" type="video/mp4">'
        'Низкое качество, полоса в районе рта</video>.\n'
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/b.mp4" type="video/mp4">'
        '3 склейки подряд</video>.\n'
    )
    result = on_page_markdown(md, None, None, None)
    assert '<div class="video-block">' in result
    assert result.count('<div class="video-item">') == 2
    assert 'src="https://example.com/a.mp4"' in result
    assert "Низкое качество, полоса в районе рта." in result
    assert "3 склейки подряд." in result
    assert '<span class="eyebrow">Примеры «Битое» (для калибровки, что считается явным браком)</span>' in result


def test_handles_wrapped_caption_and_trailing_text_after_video_tag():
    md = (
        '## Артефакты, которые всё ещё допустимы (примеры на грани)\n\n'
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/a.mp4" type="video/mp4">'
        'Мутные глаза, мелкая пиксельность, засвет сверху</video> — если мимика всё равно видна неплохо,\n'
        '  такой фрагмент разметить можно.\n'
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/b.mp4" type="video/mp4">'
        'Мелкая пиксельность, небольшая дымка на видео</video> — допустимо.\n'
    )
    result = on_page_markdown(md, None, None, None)
    assert '<div class="video-block">' in result
    assert "если мимика всё равно видна неплохо, такой фрагмент разметить можно." in result


def test_single_video_item_not_grouped():
    md = (
        "## Раздел\n\n"
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/a.mp4" type="video/mp4">Одиночный пример</video>.\n'
    )
    result = on_page_markdown(md, None, None, None)
    assert "video-block" not in result
    assert "<video" in result


def test_non_video_list_untouched():
    md = "## Раздел\n\n- обычный пункт\n- ещё один пункт\n"
    assert on_page_markdown(md, None, None, None) == md

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


def test_leading_caption_before_video_now_grouped():
    """Регрессия: manual-2-etap/11-example-library.md, раздел "Темп речи" — подпись идёт ПЕРЕД
    видео ("- **Средний темп:** <video>...</video>"), а не после. Раньше такой пункт не
    распознавался вовсе (регулярка требовала <video> сразу после "- "), весь список оставался
    нераспакованным в компактную сетку — то, что Task 10 (живая проверка) явно требует проверить
    именно для "Темп речи"."""
    md = (
        "## Темп речи\n\n"
        '- **Средний темп:** <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/mid.mp4" type="video/mp4">пример</video>\n'
        '- **Медленный темп:** <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/slow.mp4" type="video/mp4">пример</video>\n'
    )
    result = on_page_markdown(md, None, None, None)
    assert '<div class="video-block">' in result
    assert result.count('<div class="video-item">') == 2
    assert 'src="https://example.com/mid.mp4"' in result
    assert "Средний темп" in result
    assert "Медленный темп" in result


def test_trailing_non_video_item_does_not_sink_whole_list():
    """Регрессия: manual-3-etap/07-example-library.md, раздел "Антипримеры" — 8 пунктов-видео
    подряд, ЗАТЕМ один пункт-картинка (antiexample-8.jpg, источник видео не скачан, сознательно
    оставлен картинкой). Раньше однородность требовалась для ВСЕГО списка целиком — из-за одной
    картинки в конце все 8 видео тоже оставались нераспакованным вертикальным стеком
    полноразмерных плееров. Теперь прогон из 8 видео-пунктов группируется в .video-block,
    а картинка остаётся обычным пунктом списка после него."""
    md = (
        "## Примеры\n\n"
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/a.mp4" type="video/mp4">a</video> — плохое.\n'
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/b.mp4" type="video/mp4">b</video> — тоже плохое.\n'
        "- ![кадр с наложением](assets/antiexample-8.jpg)\n"
        "  Наложение кадров, сохранено как картинка.\n"
    )
    result = on_page_markdown(md, None, None, None)
    assert '<div class="video-block">' in result
    assert result.count('<div class="video-item">') == 2
    assert 'src="https://example.com/a.mp4"' in result
    assert 'src="https://example.com/b.mp4"' in result
    # картинка осталась как обычный markdown-пункт списка, не потерялась и не попала в карточку
    assert "![кадр с наложением](assets/antiexample-8.jpg)" in result
    assert "Наложение кадров, сохранено как картинка." in result


def test_leading_video_run_before_trailing_non_video_item_groups_only_the_run():
    """То же самое, но с одиночным (не сгруппированным) видео-пунктом в прогоне — прогон из
    1 видео короче порога группировки (нужно 2+), поэтому должен остаться как обычный пункт,
    а не потеряться."""
    md = (
        "## Раздел\n\n"
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/a.mp4" type="video/mp4">a</video>.\n'
        "- обычный пункт без видео.\n"
    )
    result = on_page_markdown(md, None, None, None)
    assert "video-block" not in result
    assert '<source src="https://example.com/a.mp4" type="video/mp4">' in result
    assert "обычный пункт без видео." in result


def test_eyebrow_marker_sets_label_and_is_stripped_from_output():
    """Регрессия (Concern 1 из отчёта Task 10): инжектированные превью из
    inject_example_previews.py вставляются посреди прозы без собственного markdown-заголовка,
    поэтому раньше эйброу .video-block наследовал ближайший ПРЕДЫДУЩИЙ настоящий заголовок
    страницы (например, "Уточнения по конкретным полям (памятка асессоров)" вместо "Темп речи").
    Фикс: inject_example_previews.py эмитит приватный маркер-комментарий
    "<!-- video-eyebrow: Темп речи -->" прямо перед списком; group_media_lists.py распознаёт его,
    выставляет current_heading = "Темп речи" и вырезает саму строку-маркер из вывода (она не
    должна попасть в финальный HTML — это внутренний сигнал между двумя хуками, не контент)."""
    md = (
        "## Уточнения по конкретным полям (памятка асессоров)\n\n"
        "some unrelated prose here.\n\n"
        "<!-- video-eyebrow: Темп речи -->\n"
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/a.mp4" type="video/mp4">a</video>\n'
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/b.mp4" type="video/mp4">b</video>\n'
    )
    result = on_page_markdown(md, None, None, None)
    assert '<span class="eyebrow">Темп речи</span>' in result
    assert "Уточнения по конкретным полям" not in _eyebrow_text(result)
    assert "<!-- video-eyebrow:" not in result
    assert "video-eyebrow" not in result


def _eyebrow_text(html):
    start = html.index('<span class="eyebrow">') + len('<span class="eyebrow">')
    end = html.index("</span>", start)
    return html[start:end]


def test_eyebrow_marker_does_not_leak_when_run_too_short_to_group():
    """Если после маркера прогон видео короче порога группировки (< 2), video-block не
    создаётся вовсе — но маркер-строка всё равно не должна просочиться в вывод как видимый
    текст."""
    md = (
        "## Раздел\n\n"
        "<!-- video-eyebrow: Одиночный -->\n"
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/a.mp4" type="video/mp4">a</video>\n'
    )
    result = on_page_markdown(md, None, None, None)
    assert "<!-- video-eyebrow:" not in result
    assert "video-eyebrow" not in result


def test_leading_caption_with_two_videos_in_one_item_splits_into_two_cards():
    """Тот же раздел "Темп речи": пункт "Быстрая речь" содержит ДВА видео в одном пункте списка
    (два примера через запятую) — должны получиться 2 отдельные карточки, не одна с двумя
    вложенными плеерами."""
    md = (
        "## Темп речи\n\n"
        '- **Быстрая речь:** <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/fast1.mp4" type="video/mp4">пример 1</video>, '
        '<video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/fast2.mp4" type="video/mp4">пример 2</video>\n'
        '- **Средний темп:** <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/mid.mp4" type="video/mp4">пример</video>\n'
    )
    result = on_page_markdown(md, None, None, None)
    assert '<div class="video-block">' in result
    assert result.count('<div class="video-item">') == 3
    assert 'src="https://example.com/fast1.mp4"' in result
    assert 'src="https://example.com/fast2.mp4"' in result
    assert "Быстрая речь" in result

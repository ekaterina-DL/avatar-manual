from embed_local_media import on_page_markdown as embed_local_media
from group_media_lists import on_page_markdown
from _render_helpers import render_html


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
    assert '<div class="video-block" markdown="1">' in result
    assert result.count('<div class="video-item" markdown="1">') == 2
    assert 'src="https://example.com/a.mp4"' in result
    assert "Низкое качество, полоса в районе рта." in result
    assert "3 склейки подряд." in result
    assert '<span class="eyebrow">Примеры «Битое» (для калибровки, что считается явным браком)</span>' in result


def test_rendered_html_caption_bold_markup_becomes_strong_not_literal_asterisks():
    """Fix 1 итогового обзора: markdown="1" стоял только на внутреннем <span>, а не на всех
    div-предках (.video-block/.video-grid/.video-item/.vi-cap), и подпись шла в одну строку с
    тегами — markdown="1" был мёртвым, **bold** утекал в вывод буквально. Проверяем через
    настоящий рендер (см. tests/_render_helpers.py), а не промежуточную строку хука."""
    md = (
        '## Раздел\n\n'
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/a.mp4" type="video/mp4">a — **плохое**</video>.\n'
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/b.mp4" type="video/mp4">b</video> — тоже плохое.\n'
    )
    result = on_page_markdown(md, None, None, None)
    html = render_html(result)
    assert 'markdown="1"' not in html
    assert "**" not in html
    assert "<strong>плохое</strong>" in html


def test_rendered_html_video_block_followed_by_plain_list_item_keeps_boundary_intact():
    """Регрессия-риск явно отмеченный в итоговом обзоре (Fix 1, п.3): восстановление
    markdown="1" на всех div-предках .video-block не должно склеить или сместить границу с
    ОБЫЧНЫМ пунктом списка сразу ПОСЛЕ .video-block (без пустой строки между ними) — реальный
    случай manual-3-etap/07-example-library.md, раздел "Антипримеры" (видео-прогон + картинка
    antiexample-8.jpg последним пунктом). Проверяем через настоящий рендер: закрывающий блок
    .video-block должен закрыться сам по себе, а картиночный пункт — стать отдельным <li> вне
    .video-block, а не потеряться и не оказаться внутри последней карточки."""
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
    html = render_html(result)
    assert 'markdown="1"' not in html
    assert html.count('<div class="video-item">') == 2
    # закрывающий </div> .video-block идёт до <ul> с картиночным пунктом, не внутри него
    video_block_end = html.index("</div>\n</div>\n</div>")
    ul_start = html.index("<ul>")
    assert video_block_end < ul_start
    assert '<img alt="кадр с наложением" src="assets/antiexample-8.jpg"' in html
    assert "Наложение кадров, сохранено как картинка." in html
    # картинка не осталась внутри последнего .video-item/vi-cap
    assert "antiexample-8.jpg" not in html[: html.index("<ul>")]


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
    assert '<div class="video-block" markdown="1">' in result
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
    assert '<div class="video-block" markdown="1">' in result
    assert result.count('<div class="video-item" markdown="1">') == 2
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
    assert '<div class="video-block" markdown="1">' in result
    assert result.count('<div class="video-item" markdown="1">') == 2
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


def test_narrative_qa_log_list_not_grouped():
    """Регрессия (Bug 5): manual-2-etap/10-qa-log.md, раздел "20.05.2026 — вопросы команды к
    заказчику" (реальный текст, строки 100-117). Это диалог "Вопрос -> Ответ": некоторые пункты
    цитируют .mp4-ссылку ПОСЕРЕДИНЕ полноразмерного абзаца (не "подпись + видео", а "видео —
    одна из цитат внутри рассуждения"). После того как _parse_video_item стал искать <video>
    где угодно в пункте (фикс для "Темп речи"), эти пункты стали ошибочно распознаваться как
    видео-пункты и разрывали связный список на .video-block + осколки, а в одном случае —
    ломали несбалансированный "**" из "Вопрос (про [id](url)):**" (видео вклинивается ВНУТРЬ
    жирного текста), из-за чего в подпись карточки утекал непропарсенный "**" как есть.
    Правильное поведение: список остаётся как есть (video-block НЕ создаётся), <video>
    встраивается на своём месте прямо в текст пункта, как обычный playable-элемент абзаца."""
    md = (
        '## 20.05.2026 — вопросы команды к заказчику\n\n'
        'Формат — прямой диалог (без ссылок на конкретные видео с ошибками, кроме одного примера ниже):\n\n'
        '- **Вопрос:** «Динамичный фон» так же оцениваем, как на 3-м этапе? Т.е. если незначительное\n'
        '  движение (пара листиков, далеко прошёл заблюренный человек) — ставить «естественный, но\n'
        '  статичный» или всё же «динамику»? — **Ответ:** «Да, фон оцениваем, как на 3-м этапе.»\n'
        '- **Вопрос:** если на видео много людей и они говорят/поют равномерно — сложно разметить,\n'
        '  нужно ли размечать такие сегменты? — **Ответ:** «Необходимы примеры, обычно в таких случаях\n'
        '  ориентируемся на того, кто первый начал говорить/петь, чей объём речи/пения превалирует, кто\n'
        '  виден лучше остальных и т.п. Пока берём такое.»\n'
        '- **Вопрос (с примерами качества):** [bsRaCgxTqKw](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/bsRaCgxTqKw/bsRaCgxTqKw.mp4), [_iQn2jwmNwk](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/_iQn2jwmNwk/_iQn2jwmNwk.mp4), [UAPAmMyPmDo](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/UAPAmMyPmDo/UAPAmMyPmDo.mp4), [rlVk2D1WDes](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/rlVk2D1WDes/rlVk2D1WDes.mp4) — все эти видео пойдут в артефакты на 3-м этапе, не срезаем ли мы их зря на этом этапе? — **Ответ:** «1 видео по качеству подходит, на 2-м лёгкая зернистость — допустимо, на 3-м зернистость сильнее, но есть участки, где человек перемещается, и зернистость становится некритичной.»\n'
        '- **Вопрос (про [rlVk2D1WDes](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/rlVk2D1WDes/rlVk2D1WDes.mp4)):** исполнитель отправил видео в «битое» за рамку, но в ОС пришло, что нужно разметить — окей ли, что вокруг человека такая размытость, что весь контур тела размыт? — **Ответ:** «Рамка есть только на момент заставки, далее идёт участок без рамки. Фон размыт, но лицо хорошо видно, мимика прослеживается — поэтому берём. Есть подобный пример в инструкции с комментариями. Напоминаем: мы оцениваем не всё видео целиком (как на 3 этапе), а высматриваем подходящий сегмент. Если такого сегмента нет — только тогда бракуем видео.»\n'
        '- **Уточнение поля «Фон»:** «У нас на 2 этапе не просто „динамичный“, там через слэш идёт\n'
        '  „уличный“. Т.е. если на видео есть признаки того, что человек находится на улице, ставим\n'
        '  „Динамичный/уличный“ — здесь неважно, есть ли дуновение ветра или нет.» ⚠️ Важное уточнение:\n'
        '  **сама по себе съёмка на улице** (даже статичная, без движения) уже требует значения\n'
        '  «Динамичный/уличный» — см. [04-classifier.md](04-classifier.md#уточнения-по-конкретным-полям-памятка-асессоров).\n'
    )
    embedded = embed_local_media(md, None, None, None)
    result = on_page_markdown(embedded, None, None, None)
    assert "video-block" not in result
    # видео остаются встроенными плеерами прямо в тексте пункта, просто без сетки
    assert result.count("<video") == 5
    assert 'src="https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/bsRaCgxTqKw/bsRaCgxTqKw.mp4"' in result
    # список не развалился — все исходные пункты и связный диалог "Вопрос -> Ответ" целы
    assert result.count("- **Вопрос") == 4
    assert "- **Уточнение поля «Фон»:**" in result


def test_narrative_common_mistakes_list_not_grouped():
    """Регрессия (Bug 5): manual-3-etap/03-common-mistakes.md, раздел "Калиброванные примеры
    (реальные проверенные кейсы)" (реальный текст, строки 37-76). 12 пунктов, каждый — цельный
    абзац-разбор кейса, некоторые из них дополнительно ссылаются на .mp4-пример в скобках в
    конце. Раньше два прогона таких пунктов (с примером) ошибочно вырывались в 2 отдельных
    .video-block, разрывая единый список на несвязные осколки. Правильное поведение: список
    остаётся цельным, video-block не создаётся вовсе — ни один пункт не является чистой
    "подпись + видео" карточкой (у всех — полноразмерный абзац с подписью и до, и после видео)."""
    md = (
        '## Калиброванные примеры (реальные проверенные кейсы)\n\n'
        '- **Ракурс:** slight_turn, если не видно второго уха; профиль встречается редко — выбираем\n'
        '  превалирующий по ролику ракурс, а не единичный кадр\n'
        '  ([пример](https://obs.ru-moscow-1.hc.sbercloud.ru/gigaeye-kandinsky-spark/ak/avatar/1f4a641f-d256-41d3-b00a-8b246d8fec99/trimmed/-131143144_456240365__segment_2_30_233__seg2.mp4)).\n'
        '- **Использование микрофона:** петличный микрофон, закреплённый на рубашке, — частая ошибка\n'
        '  (не отмечают его использование). Проверяйте внимательно даже неочевидные случаи\n'
        '  ([пример](https://obs.ru-moscow-1.hc.sbercloud.ru/gigaeye-kandinsky-spark/ak/avatar/0be25d06-671a-4512-b731-e5f5aaeef217/trimmed/-86457930_456239083__segment_1_72_91__seg1.mp4)).\n'
        '- **Субтитры/текст:** пропуск наложенного текста — грубая ошибка, отмечается в любом случае,\n'
        '  даже если текст на экране недолго (тот же пример, что и про микрофон — там же пропущен текст).\n'
        '- **Сколько людей в кадре:** если второй человек в кадре молчит, но активно невербально\n'
        '  проявляет интерес к говорящему (мимика, реакция) — это уже `multiple_distracting`, а не\n'
        '  `multiple_static`.\n'
        '- **Вид съёмки:** видео с надписью в кадре (например, титры/подпись) может относиться к\n'
        '  `news_broadcast`, даже если по остальным признакам похоже на интервью.\n'
        '- **Вид съёмки (ещё пример):** видео с медленной речью, любительской съёмкой (нет проф.\n'
        '  студийного оформления) и профилем (почти не видно обоих глаз) — вид съёмки amateur, эмоция\n'
        '  «other» (торжественность при чтении не подходит под перечисленные), плюс отмечен артефакт\n'
        '  ([пример](https://obs.ru-moscow-1.hc.sbercloud.ru/gigaeye-kandinsky-spark/ak/avatar/0c8de823-1003-4be0-9f16-b8ac600b0791/trimmed/-167333217_456239754__segment_1_1_173.mp4)).\n'
        '- **Вид съёмки (ещё пример):** хороший свет и средний темп речи — ближе к `professional_interview`,\n'
        '  чем к «любительской», хотя формально условия скромные\n'
        '  ([пример](https://obs.ru-moscow-1.hc.sbercloud.ru/gigaeye-kandinsky-spark/ak/avatar/0c8de823-1003-4be0-9f16-b8ac600b0791/trimmed/-167333217_456239831__segment_2_36_57__seg2.mp4)).\n'
        '- **Эмоция + завершённость мысли + движение + вид съёмки** — реальный набор ответов по одному\n'
        '  ролику: нейтральная эмоция (счастье не прослеживается, хотя ожидалось), незавершённая мысль,\n'
        '  medium (подключены жесты руками), вид съёмки — скорее образовательное видео\n'
        '  ([пример](https://obs.ru-moscow-1.hc.sbercloud.ru/gigaeye-kandinsky-spark/ak/avatar/1f4a641f-d256-41d3-b00a-8b246d8fec99/trimmed/-144892536_456239685__segment_1_8_35.mp4)).\n'
        '- **Битое — низкое качество:** сильная пиксельность + тусклое освещение, усиливающее\n'
        '  пикселизацию, из-за чего не распознаются черты лица\n'
        '  ([пример](https://obs.ru-moscow-1.hc.sbercloud.ru/gigaeye-kandinsky-spark/ak/avatar/1c35b7ef-b71d-48fc-94a7-b11274ce1cad/trimmed/113690075_456239171__segment_1_0_129.mp4)).\n'
        '- **Битое — чёрный кадр в начале:** участок чёрного цвета без персонажа в начале ролика — такие\n'
        '  видео бракуются сразу, даже если далее качество нормальное\n'
        '  ([пример](https://obs.ru-moscow-1.hc.sbercloud.ru/gigaeye-kandinsky-spark/ak/avatar/1c35b7ef-b71d-48fc-94a7-b11274ce1cad/trimmed/219338794_456239316__segment_1_0_11.mp4)).\n'
        '- **Битое — смазанность:** очень большая смазанность, черты лица теряются (в одном случае у\n'
        '  человека «стёрся» глаз)\n'
        '  ([пример](https://obs.ru-moscow-1.hc.sbercloud.ru/gigaeye-kandinsky-spark/ak/avatar/1c35b7ef-b71d-48fc-94a7-b11274ce1cad/trimmed/-85053588_456239019__segment_2_79_90__seg2.mp4)).\n'
        '- **Наложение речи + количество говорящих:** быстрая речь одного человека («тараторит», но с\n'
        '  паузами) + наложение фоновых голосов — в поле «количество говорящих» всё равно ставим 1\n'
        '  (разговоры на фоне в этом критерии не оцениваем), а наложение фиксируем отдельным полем.\n'
        '\n'
        '`[ОС Аватар примеры 3 этап (1) и (2)]`\n'
    )
    embedded = embed_local_media(md, None, None, None)
    result = on_page_markdown(embedded, None, None, None)
    assert "video-block" not in result
    assert result.count("<video") == 8
    # все 12 пунктов списка целы и на своих местах, список не разорван на осколки
    assert result.count("\n- **") == 12
    assert "- **Ракурс:**" in result
    assert "- **Наложение речи + количество говорящих:**" in result


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
    assert '<div class="video-block" markdown="1">' in result
    assert result.count('<div class="video-item" markdown="1">') == 3
    assert 'src="https://example.com/fast1.mp4"' in result
    assert 'src="https://example.com/fast2.mp4"' in result
    assert "Быстрая речь" in result

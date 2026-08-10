from friendly_md_link_text import on_page_markdown


class FakeFile:
    def __init__(self, src_uri):
        self.src_uri = src_uri


class FakePage:
    def __init__(self, src_uri):
        self.file = FakeFile(src_uri)


def test_same_folder_bare_filename_becomes_title():
    page = FakePage("manual-2-etap/09-disputed-points.md")
    md = "См. [04-classifier.md](04-classifier.md#памятка)."
    result = on_page_markdown(md, page, None, None)
    assert result == "См. [Классификатор](04-classifier.md#памятка)."


def test_same_folder_repeated_anchors_all_get_page_title():
    page = FakePage("manual-2-etap/09-disputed-points.md")
    md = "См. [10-qa-log.md](10-qa-log.md#0607-2026) и [10-qa-log.md](10-qa-log.md#21052026)."
    result = on_page_markdown(md, page, None, None)
    assert result == "См. [Журнал проверок ОС](10-qa-log.md#0607-2026) и [Журнал проверок ОС](10-qa-log.md#21052026)."


def test_cross_folder_link_gets_stage_suffix():
    page = FakePage("manual-2-etap/00-overview.md")
    md = "[../manual-3-etap/00-overview.md](../manual-3-etap/00-overview.md)"
    result = on_page_markdown(md, page, None, None)
    assert result == "[Обзор проекта (3 этап)](../manual-3-etap/00-overview.md)"


def test_resolves_target_from_href_even_when_text_has_no_prefix():
    # Реальный случай из manual-3-etap/01-classifier.md: видимый текст без manual-2-etap/
    # префикса, целевая папка видна только из href.
    page = FakePage("manual-3-etap/01-classifier.md")
    md = "[09-disputed-points.md](../manual-2-etap/09-disputed-points.md#поле-объём)"
    result = on_page_markdown(md, page, None, None)
    assert result == "[Спорные моменты (2 этап)](../manual-2-etap/09-disputed-points.md#поле-объём)"


def test_bold_wrapped_link_still_matched():
    page = FakePage("manual-3-etap/03-common-mistakes.md")
    md = "вынесены в отдельный файл **[05-faq.md](05-faq.md)**."
    result = on_page_markdown(md, page, None, None)
    assert result == "вынесены в отдельный файл **[Разбор кейсов (FAQ)](05-faq.md)**."


def test_unknown_target_left_untouched():
    page = FakePage("manual-3-etap/03-common-mistakes.md")
    md = "в [_sources-log.md](_sources-log.md))."
    result = on_page_markdown(md, page, None, None)
    assert result == md


def test_filename_with_trailing_words_replaced_whole():
    # Реальный случай в manual-3-etap/00-overview.md: к имени файла вручную дописаны слова
    # "2 этапа" — не должно получиться задвоение с автоматической пометкой "(2 этап)".
    page = FakePage("manual-3-etap/00-overview.md")
    md = "см. [00-overview.md 2 этапа](../manual-2-etap/00-overview.md#как-устроено-оспаривание-ошибки-механика-апелляций)."
    result = on_page_markdown(md, page, None, None)
    assert result == (
        "см. [Обзор проекта (2 этап)]"
        "(../manual-2-etap/00-overview.md#как-устроено-оспаривание-ошибки-механика-апелляций)."
    )


def test_trailing_stage_word_outside_brackets_not_duplicated():
    # Реальный случай в manual-3-etap/00-overview.md: автор вручную дописал "2 этапа" СНАРУЖИ
    # скобок ссылки — без дедупликации получилось бы "Обзор проекта (2 этап) 2 этапа".
    page = FakePage("manual-3-etap/00-overview.md")
    md = "(см. [00-overview.md](../manual-2-etap/00-overview.md#порог) 2 этапа)"
    result = on_page_markdown(md, page, None, None)
    assert result == "(см. [Обзор проекта (2 этап)](../manual-2-etap/00-overview.md#порог))"


def test_trailing_stage_word_mismatched_digit_is_kept():
    # Число в хвосте не совпадает с этапом цели ссылки (тут ссылка ведёт на 2 этап, а хвост
    # говорит "3 этапа") — считаем это НЕ дублирующей пометкой, текст хвоста не трогаем.
    page = FakePage("manual-3-etap/00-overview.md")
    md = "(см. [04-classifier.md](../manual-2-etap/04-classifier.md) 3 этапа)"
    result = on_page_markdown(md, page, None, None)
    assert result == "(см. [Классификатор (2 этап)](../manual-2-etap/04-classifier.md) 3 этапа)"


def test_regular_prose_link_untouched():
    page = FakePage("index.md")
    md = "[2 этап →](manual-2-etap/00-overview.md)"
    result = on_page_markdown(md, page, None, None)
    assert result == md

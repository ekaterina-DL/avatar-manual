from fix_stage_relationship import on_page_markdown

OVERVIEW_INTRO = (
    "# Обзор проекта «Аватар»\n\n"
    "> ⚠️ **Этот мануал — только про 2 этап** (заявки 26-28). У проекта есть отдельный, более ранний\n"
    "> и параллельный **3 этап** (заявка 46) — другая цель, другой классификатор (19 вопросов),\n"
    "> частично другие критерии брака (например, виньетка на видео там считается «битым», а здесь —\n"
    "> нет). Материал по 3 этапу сознательно вынесен в отдельный мануал —\n"
    "> [../manual-3-etap/00-overview.md](../manual-3-etap/00-overview.md) — чтобы не путать\n"
    "> исполнителей 2 этапа требованиями, которые к ним не относятся.\n\n"
    "## Цель проекта\n"
)


class FakeFile:
    def __init__(self, src_uri):
        self.src_uri = src_uri


class FakePage:
    def __init__(self, src_uri):
        self.file = FakeFile(src_uri)


def test_removes_more_earlier_and_parallel_claim():
    page = FakePage("manual-2-etap/00-overview.md")
    result = on_page_markdown(OVERVIEW_INTRO, page, None, None)
    assert "более ранний" not in result
    assert "параллельный **3 этап**" not in result
    assert "идёт следующим шагом сразу после 2 этапа" in result
    assert "там размечают уже нарезанные на\n> 2 этапе сегменты" in result


def test_keeps_the_rest_of_the_intro_and_link():
    page = FakePage("manual-2-etap/00-overview.md")
    result = on_page_markdown(OVERVIEW_INTRO, page, None, None)
    assert "другой классификатор (19 вопросов)" in result
    assert "[../manual-3-etap/00-overview.md](../manual-3-etap/00-overview.md)" in result
    assert "## Цель проекта" in result


def test_untouched_on_other_pages():
    page = FakePage("manual-3-etap/00-overview.md")
    result = on_page_markdown(OVERVIEW_INTRO, page, None, None)
    assert result == OVERVIEW_INTRO


def test_noop_if_source_text_already_changed():
    page = FakePage("manual-2-etap/00-overview.md")
    changed = "# Обзор\n\nЧто-то совсем другое про этапы.\n"
    result = on_page_markdown(changed, page, None, None)
    assert result == changed

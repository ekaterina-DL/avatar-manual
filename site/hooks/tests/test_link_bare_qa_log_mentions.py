from link_bare_qa_log_mentions import on_page_markdown


class FakeFile:
    def __init__(self, src_uri):
        self.src_uri = src_uri


class FakePage:
    def __init__(self, src_uri):
        self.file = FakeFile(src_uri)


def test_links_bare_common_mistakes_mention():
    page = FakePage("manual-2-etap/10-qa-log.md")
    md = "официальную инструкцию как иллюстрации (Топ-5 в 06-common-mistakes.md ссылается на те же\nвидео от 15.05.2026)."
    result = on_page_markdown(md, page, None, None)
    assert "[Частые ошибки](06-common-mistakes.md) ссылается на те же" in result
    assert "06-common-mistakes.md ссылается" not in result.replace(
        "[Частые ошибки](06-common-mistakes.md)", ""
    )


def test_links_all_three_bare_faq_mentions_in_table():
    page = FakePage("manual-2-etap/10-qa-log.md")
    md = (
        "| Монолог подготовленный (см. разбор в 07-faq.md — как отличить без знания языка). |\n"
        "| Фон не динамичный/уличный (см. разбор в 07-faq.md — лёгкие раздражители на фоне). |\n"
        "| Видео отправлено в битое (см. разбор в 07-faq.md — заказчик не согласился). |\n"
    )
    result = on_page_markdown(md, page, None, None)
    assert result.count("[07-faq.md](07-faq.md)") == 3
    assert "как отличить без знания языка" in result
    assert "лёгкие раздражители на фоне" in result
    assert "заказчик не согласился" in result


def test_untouched_on_other_pages():
    page = FakePage("manual-2-etap/06-common-mistakes.md")
    md = "см. разбор в 07-faq.md — что-то."
    result = on_page_markdown(md, page, None, None)
    assert result == md


def test_existing_real_links_in_file_not_double_wrapped():
    page = FakePage("manual-2-etap/10-qa-log.md")
    md = "не смешивать с общей статистикой в\n[06-common-mistakes.md](06-common-mistakes.md). Часть этих же примеров."
    result = on_page_markdown(md, page, None, None)
    assert result == md

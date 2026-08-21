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


def test_untouched_on_other_pages():
    page = FakePage("manual-2-etap/06-common-mistakes.md")
    md = "официальную инструкцию как иллюстрации (Топ-5 в 06-common-mistakes.md ссылается на те же видео)."
    result = on_page_markdown(md, page, None, None)
    assert result == md


def test_existing_real_links_in_file_not_double_wrapped():
    page = FakePage("manual-2-etap/10-qa-log.md")
    md = "не смешивать с общей статистикой в\n[06-common-mistakes.md](06-common-mistakes.md). Часть этих же примеров."
    result = on_page_markdown(md, page, None, None)
    assert result == md

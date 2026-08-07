from hide_site_only_sections import on_page_markdown

OVERVIEW_2ETAP = """# Обзор

## Порог качества по ходу работы (не путать с порогом экзамена)

Текст порога качества.

## История проекта: этапы во времени

Текст истории, не должен остаться.

## Обучение и входной экзамен «Ступень 2»

Текст обучения.

## Как читать этот мануал

Текст про то как читать.
"""


class FakeFile:
    def __init__(self, src_uri):
        self.src_uri = src_uri


class FakePage:
    def __init__(self, src_uri):
        self.file = FakeFile(src_uri)


class FakeSiteDir:
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return self._value


class FakeConfig(dict):
    def __init__(self, site_dir):
        super().__init__()
        self.site_dir = FakeSiteDir(site_dir)


def test_removes_both_sections_on_site_build():
    page = FakePage("manual-2-etap/00-overview.md")
    config = FakeConfig("/repo/avatar-manual-build/build")
    result = on_page_markdown(OVERVIEW_2ETAP, page, config, None)
    assert "История проекта" not in result
    assert "Как читать этот мануал" not in result
    assert "Текст порога качества." in result
    assert "Текст обучения." in result


def test_untouched_on_pdf_build():
    page = FakePage("manual-2-etap/00-overview.md")
    config = FakeConfig("/repo/avatar-manual-build/build-pdf")
    result = on_page_markdown(OVERVIEW_2ETAP, page, config, None)
    assert result == OVERVIEW_2ETAP


def test_untouched_on_unrelated_page():
    page = FakePage("manual-2-etap/01-general-requirements.md")
    config = FakeConfig("/repo/avatar-manual-build/build")
    result = on_page_markdown(OVERVIEW_2ETAP, page, config, None)
    assert result == OVERVIEW_2ETAP

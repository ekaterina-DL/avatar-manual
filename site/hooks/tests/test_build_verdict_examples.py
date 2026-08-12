from build_verdict_examples import on_page_markdown
from _render_helpers import render_html

VIDEO_1 = ('<video controls preload="metadata" style="max-width:100%">'
           '<source src="https://a.mp4" type="video/mp4">видео</video>')
VIDEO_2 = ('<video controls preload="metadata" style="max-width:100%">'
           '<source src="https://b.mp4" type="video/mp4">видео</video>')
VIDEO_3 = ('<video controls preload="metadata" style="max-width:100%">'
           '<source src="https://c.mp4" type="video/mp4">видео</video>')

TABLE_MD = (
    "Текст перед таблицей.\n\n"
    "| Вердикт заказчика | Признак | Пример |\n"
    "|---|---|---|\n"
    f"| Битое | Критичная пикселизация | {VIDEO_1} |\n"
    f"| Подходящее видео | Хорошее качество | {VIDEO_2} |\n"
    f"| Артефакт (не битое) | **Небольшой** дефект | {VIDEO_3} |\n"
    "\n"
    "Текст после таблицы.\n"
)


class FakeFile:
    src_uri = "manual-3-etap/03-common-mistakes.md"


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


SITE_CONFIG = FakeConfig("/repo/avatar-manual-build/build")
PDF_CONFIG = FakeConfig("/repo/avatar-manual-build/build-pdf")


def test_table_becomes_example_grid_with_three_verdicts():
    result = on_page_markdown(TABLE_MD, FakePage(), SITE_CONFIG, None)
    assert '<div class="example-grid" markdown="1">' in result
    assert '<div class="example-card bad" markdown="1">' in result
    assert '<div class="example-card good" markdown="1">' in result
    assert '<div class="example-card warn" markdown="1">' in result
    assert result.count('<div class="example-card') == 3


def test_verdict_tags_present():
    result = on_page_markdown(TABLE_MD, FakePage(), SITE_CONFIG, None)
    assert "🚫 Битое" in result
    assert "✅ Подходящее" in result
    assert "🟡 Артефакт" in result


def test_video_tags_preserved():
    result = on_page_markdown(TABLE_MD, FakePage(), SITE_CONFIG, None)
    assert VIDEO_1 in result
    assert VIDEO_2 in result
    assert VIDEO_3 in result


def test_feature_text_preserved():
    result = on_page_markdown(TABLE_MD, FakePage(), SITE_CONFIG, None)
    assert "Критичная пикселизация" in result
    assert "Хорошее качество" in result
    assert "**Небольшой** дефект" in result


def test_surrounding_text_preserved():
    result = on_page_markdown(TABLE_MD, FakePage(), SITE_CONFIG, None)
    assert "Текст перед таблицей." in result
    assert "Текст после таблицы." in result


def test_untouched_on_other_pages():
    class OtherFile:
        src_uri = "manual-3-etap/07-example-library.md"

    class OtherPage:
        file = OtherFile()

    assert on_page_markdown(TABLE_MD, OtherPage(), SITE_CONFIG, None) == TABLE_MD


def test_noop_on_pdf_build():
    result = on_page_markdown(TABLE_MD, FakePage(), PDF_CONFIG, None)
    assert result == TABLE_MD


def test_table_without_matching_header_untouched():
    md = "| Другая | Таблица |\n|---|---|\n| a | b |\n"
    assert on_page_markdown(md, FakePage(), SITE_CONFIG, None) == md


def test_rendered_html_bold_in_feature_becomes_strong():
    result = on_page_markdown(TABLE_MD, FakePage(), SITE_CONFIG, None)
    html = render_html(result)
    assert 'markdown="1"' not in html
    assert "<strong>Небольшой</strong> дефект" in html

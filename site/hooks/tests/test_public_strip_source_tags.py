from public_strip_source_tags import on_page_content
from test_public_drop_stage3 import PDF, PUBLIC, SITE

HTML = (
    '<p>Правило про сегменты.\n<span class="source-tag">[Инстр. Компания, стр.1]</span></p>\n'
    '<p><span class="source-tag">[Переписка с заказчиком,\n05.08.2026]</span></p>\n'
    "<p>Следующий абзац.</p>"
)


def test_public_build_strips_tags_and_empty_paragraphs():
    result = on_page_content(HTML, None, PUBLIC, None)
    assert "source-tag" not in result
    assert "Компания" not in result
    assert "Переписка" not in result
    assert "<p></p>" not in result
    assert "Правило про сегменты." in result
    assert "<p>Следующий абзац.</p>" in result


def test_normal_and_pdf_builds_untouched():
    assert on_page_content(HTML, None, SITE, None) == HTML
    assert on_page_content(HTML, None, PDF, None) == HTML

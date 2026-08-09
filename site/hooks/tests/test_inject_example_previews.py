from pathlib import Path

import pytest

from inject_example_previews import on_page_markdown, MAPPINGS

FIXTURES = Path(__file__).parent / "fixtures"


class FakeFile:
    def __init__(self, src_uri):
        self.src_uri = src_uri


class FakePage:
    def __init__(self, src_uri):
        self.file = FakeFile(src_uri)


@pytest.fixture(autouse=True)
def _docs_dir(monkeypatch):
    import inject_example_previews as mod

    monkeypatch.setattr(mod, "DOCS_DIR", FIXTURES)


def test_classifier_tempo_preview_inserted_after_anchor():
    target_md = (
        "- **Темп речи:** быстрый / медленный (цель по команде в целом — "
        "равномерное распределение).\n"
        "- **Язык и акценты:** русский / английский / другое.\n"
    )
    page = FakePage("manual-2-etap/04-classifier.md")
    result = on_page_markdown(target_md, page, None, None)
    assert "example1.mp4" in result
    assert "→ ещё" in result
    assert result.index("Темп речи:") < result.index("example1.mp4")
    assert result.index("example1.mp4") < result.index("Язык и акценты:")


def test_mapping_table_covers_expected_targets():
    targets = {m["target_file"] for m in MAPPINGS}
    assert "manual-2-etap/04-classifier.md" in targets
    assert "manual-3-etap/04-video-quality.md" in targets


def test_untouched_on_unrelated_page():
    md = "Обычный текст."
    page = FakePage("manual-2-etap/07-faq.md")
    assert on_page_markdown(md, page, None, None) == md


def test_preview_with_no_remaining_items_has_blank_line_before_closing_div():
    """Регрессия: когда в разделе-источнике примеров не больше, чем max_items (remaining == 0,
    строка "→ ещё N прим." не добавляется), закрывающий </div> должен всё равно отделяться
    пустой строкой от последнего пункта списка. Без неё group_media_lists.py (следующий хук в
    пайплайне) ошибочно затягивает "</div>" внутрь подписи последнего видео-пункта — см.
    test_injected_preview_survives_group_media_lists_without_broken_html ниже, где
    воспроизводится именно это взаимодействие двух хуков."""
    from inject_example_previews import MAPPINGS

    mapping = next(m for m in MAPPINGS if m["source_heading"] == "Ракурс")
    target_md = (
        "- **Группа данных:** «Студия» / «Естественная среда».\n"
        "- **Речь / Пение:** взаимоисключающие варианты.\n"
    )
    page = FakePage(mapping["target_file"])
    result = on_page_markdown(target_md, page, None, None)
    # remaining должен быть 0 для фикстуры "Ракурс" (ровно 2 примера = max_items)
    assert "→ ещё" not in result
    assert "\n\n</div>" in result, (
        "закрывающий </div> должен идти после пустой строки, а не сразу после "
        "последнего video-item"
    )


def test_injected_preview_survives_group_media_lists_without_broken_html():
    """Интеграционная регрессия на реальное взаимодействие двух хуков в порядке mkdocs.yml:
    inject_example_previews → (embed_local_media в реальном пайплайне превращает голые .mp4
    в <video>) → group_media_lists. Раньше на этой цепочке для превью "Ракурс" получался битый
    вложенный HTML `<div class="vi-cap"><span markdown="1"></div></span></div>`."""
    import embed_local_media
    import group_media_lists
    from inject_example_previews import MAPPINGS

    mapping = next(m for m in MAPPINGS if m["source_heading"] == "Ракурс")
    target_md = (
        "## Уточнения\n\n"
        "- **Группа данных:** «Студия» / «Естественная среда».\n"
        "- **Речь / Пение:** взаимоисключающие варианты.\n"
    )
    page = FakePage(mapping["target_file"])
    md = on_page_markdown(target_md, page, None, None)
    md = embed_local_media.on_page_markdown(md, page, None, None)
    result = group_media_lists.on_page_markdown(md, page, None, None)

    assert "</div></span>" not in result, "битая вложенность vi-cap/span не должна встречаться"
    assert 'exampleA.mp4' in result
    assert 'exampleB.mp4' in result

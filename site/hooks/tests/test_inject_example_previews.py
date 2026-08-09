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

import json
import re

from build_quiz_bank import on_page_markdown, build_bank, TARGET_PAGE, SOURCE_FILES
from build_quiz_bank import extract_numbers, extract_forbidden_tags

SEGMENTS_KEYFACTS = """# Сегменты

<div class="keyfacts">
<div class="kf-stat">
<div class="kf-value">10–300<span>сек</span></div>
<div class="kf-label">длительность одного сегмента</div>
</div>
<div class="kf-stat">
<div class="kf-value">10<span>сегментов</span></div>
<div class="kf-label">максимум на одном видео</div>
</div>
<div class="kf-forbid">
<div class="kf-tags">
<span class="kf-tag">смену кадра</span>
<span class="kf-tag">склейки</span>
<span class="kf-tag">закадровый голос</span>
<span class="kf-tag">молчание &gt;4 сек и на границах</span>
</div>
</div>
</div>
"""

CLASSIFIER_FIELDS = """# Заполнение классификатора

Классификатор в интерфейсе разметки состоит из **13 полей**. Ниже — каждое поле по порядку.
"""


def test_extract_numbers_segment_duration():
    qs = extract_numbers({"manual-2-etap/02-segments.md": SEGMENTS_KEYFACTS})
    dur = [q for q in qs if "длительност" in q["question"].lower()]
    assert dur, qs
    q = dur[0]
    assert q["category"] == "DE"
    assert q["options"][q["answer"]] == q["options"][0]
    assert "300" in q["options"][0]
    assert len(q["options"]) >= 3
    assert q["review"]["url"].startswith("02-segments.md#")


def test_extract_numbers_recipe_drops_when_number_absent():
    # В тексте нет "13 полей" -> рецепт про число полей не выдаёт вопрос
    qs = extract_numbers({"manual-2-etap/04-classifier.md": "# Классификатор\n\nбез числа полей\n"})
    assert not [q for q in qs if "полей" in q["question"].lower()]


def test_extract_numbers_classifier_field_count_present():
    qs = extract_numbers({"manual-2-etap/04-classifier.md": CLASSIFIER_FIELDS})
    fld = [q for q in qs if "полей" in q["question"].lower()]
    assert fld and fld[0]["options"][0] == "13"


def test_extract_forbidden_tags():
    qs = extract_forbidden_tags({"manual-2-etap/02-segments.md": SEGMENTS_KEYFACTS})
    assert qs
    q = qs[0]
    assert q["category"] == "DE"
    assert len(q["options"]) >= 3
    # верный вариант — один из запрещённых тегов
    assert q["options"][0] in {"смену кадра", "склейки", "закадровый голос",
                               "молчание >4 сек и на границах"} or "молчание" in q["options"][0]
    # неверные варианты — «допустимые» вещи, не из списка тегов
    assert "пиксельность на фоне" in q["options"] or "лёгкий фоновый шум" in q["options"]


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
    def __init__(self, site_dir, docs_dir):
        super().__init__()
        self.site_dir = FakeSiteDir(site_dir)
        self["docs_dir"] = docs_dir


PAGE_MD = "# Тестирование\n\nвведение\n\n<!-- QUIZ-BANK -->\n"


def _bank_from_html(html):
    m = re.search(
        r'<script id="quiz-bank" type="application/json">(.*?)</script>', html, re.S
    )
    assert m, html
    return json.loads(m.group(1))


def test_injects_empty_bank_on_target_page(tmp_path):
    cfg = FakeConfig(str(tmp_path / "build"), str(tmp_path))
    out = on_page_markdown(PAGE_MD, FakePage(TARGET_PAGE), cfg, None)
    bank = _bank_from_html(out)
    assert bank["questions"] == []
    assert "generatedAt" in bank
    assert "<!-- QUIZ-BANK -->" not in out


def test_noop_on_other_pages(tmp_path):
    cfg = FakeConfig(str(tmp_path / "build"), str(tmp_path))
    md = "# Другая страница\n\n<!-- QUIZ-BANK -->\n"
    out = on_page_markdown(md, FakePage("manual-2-etap/02-segments.md"), cfg, None)
    assert out == md


def test_pdf_profile_replaces_with_note(tmp_path):
    cfg = FakeConfig(str(tmp_path / "build-pdf"), str(tmp_path))
    out = on_page_markdown(PAGE_MD, FakePage(TARGET_PAGE), cfg, None)
    assert "quiz-bank" not in out
    assert "только на сайте" in out.lower()


def test_source_files_exclude_overview():
    assert not any(f.endswith("00-overview.md") for f in SOURCE_FILES)
    assert "manual-2-etap/02-segments.md" in SOURCE_FILES


def test_build_bank_shape():
    bank = build_bank(sources={}, manual_yaml_text="")
    assert bank["questions"] == []
    assert isinstance(bank["generatedAt"], str)

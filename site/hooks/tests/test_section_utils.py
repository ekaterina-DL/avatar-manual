from _section_utils import extract_section, strip_section

SAMPLE = """# Заголовок файла

## Раздел A

Текст A, строка 1.
Текст A, строка 2.

## Раздел Б

Текст Б.

### Подраздел Б.1

Текст подраздела.

## Раздел В

Текст В.
"""


def test_extract_middle_section_stops_before_next_heading_same_level():
    body = extract_section(SAMPLE, "Раздел A")
    assert "Текст A, строка 1." in body
    assert "Раздел Б" not in body


def test_extract_section_includes_deeper_subheadings():
    body = extract_section(SAMPLE, "Раздел Б")
    assert "Подраздел Б.1" in body
    assert "Текст подраздела." in body
    assert "Раздел В" not in body


def test_extract_last_section_goes_to_end_of_file():
    body = extract_section(SAMPLE, "Раздел В")
    assert "Текст В." in body


def test_extract_missing_heading_returns_none():
    assert extract_section(SAMPLE, "Нет такого раздела") is None


def test_strip_section_removes_heading_and_body():
    result = strip_section(SAMPLE, "Раздел Б")
    assert "Раздел Б" not in result
    assert "Подраздел Б.1" not in result
    assert "Раздел A" in result
    assert "Раздел В" in result


def test_strip_missing_heading_is_noop():
    assert strip_section(SAMPLE, "Нет такого раздела") == SAMPLE

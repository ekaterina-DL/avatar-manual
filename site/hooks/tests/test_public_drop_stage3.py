from public_drop_stage3 import on_page_markdown

INDEX_MD = """# Мануал асессора «Аватар»

Проект состоит из двух независимых этапов с разными классификаторами и правилами.
Выберите свой этап:

## [2 этап →](manual-2-etap/00-overview.md)

Заявки 26, 27, 28. Поиск подходящего сегмента внутри длинного видео.

## [3 этап →](manual-3-etap/00-overview.md)

Заявка 46. Классификация уже нарезанного фрагмента целиком.

---

Не уверены, какой у вас этап? Спросите руководителя проекта.
"""

OVERVIEW_2ETAP = """# Обзор

На 2 этапе каждое задание выполняет **один** асессор — в отличие от 3 этапа, где их три
(тройное перекрытие, см. [мануал 3 этапа](../manual-3-etap/00-overview.md#нормативы)).

Материал по 3 этапу вынесен в отдельный мануал —
[Обзор проекта (3 этап)](../manual-3-etap/00-overview.md).
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


PUBLIC = FakeConfig("/repo/avatar-manual-build/build-public")
SITE = FakeConfig("/repo/avatar-manual-build/build")
PDF = FakeConfig("/repo/avatar-manual-build/build-pdf")


# --- index.md: блок «выбор этапа» про 3 этап ------------------------------------------------

def test_index_drops_stage3_block_on_public_build():
    result = on_page_markdown(INDEX_MD, FakePage("index.md"), PUBLIC, None)
    assert "3 этап" not in result
    assert "Заявка 46" not in result
    assert "manual-3-etap" not in result
    # блок 2 этапа, разделитель и подсказка остаются
    assert "## [2 этап →](manual-2-etap/00-overview.md)" in result
    assert "Поиск подходящего сегмента внутри длинного видео." in result
    assert "\n---\n" in result
    assert "Не уверены, какой у вас этап?" in result


def test_index_untouched_on_normal_build():
    assert on_page_markdown(INDEX_MD, FakePage("index.md"), SITE, None) == INDEX_MD


def test_index_untouched_on_pdf_build():
    assert on_page_markdown(INDEX_MD, FakePage("index.md"), PDF, None) == INDEX_MD


def test_index_without_stage3_heading_does_not_crash():
    already = "# Мануал\n\n## [2 этап →](manual-2-etap/00-overview.md)\n\nТекст.\n"
    assert on_page_markdown(already, FakePage("index.md"), PUBLIC, None) == already


# --- перекрёстные ссылки на 3 этап на страницах 2 этапа ------------------------------------

def test_stage3_links_become_plain_text_on_public_build():
    result = on_page_markdown(OVERVIEW_2ETAP, FakePage("manual-2-etap/00-overview.md"), PUBLIC, None)
    assert "](../manual-3-etap/" not in result
    assert "manual-3-etap" not in result
    # видимый текст ссылки сохранён
    assert "см. мануал 3 этапа)" in result
    assert "отдельный мануал —\nОбзор проекта (3 этап)." in result


def test_stage3_links_untouched_on_normal_build():
    result = on_page_markdown(OVERVIEW_2ETAP, FakePage("manual-2-etap/00-overview.md"), SITE, None)
    assert result == OVERVIEW_2ETAP


def test_page_without_stage3_links_untouched_on_public_build():
    md = "# Сегменты\n\nСм. [классификатор](04-classifier.md).\n"
    assert on_page_markdown(md, FakePage("manual-2-etap/02-segments.md"), PUBLIC, None) == md

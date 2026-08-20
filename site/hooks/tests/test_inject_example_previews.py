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
        "### Темп речи\n\n"
        "Значения: Медленный / Быстрый.\n\n"
        "### Язык и акценты\n\n"
        "Значения: Русский / Английский / Другой.\n"
    )
    page = FakePage("manual-2-etap/04-classifier.md")
    result = on_page_markdown(target_md, page, None, None)
    assert "example1.mp4" in result
    assert "→ ещё" in result
    assert result.index("Темп речи") < result.index("example1.mp4")
    assert result.index("example1.mp4") < result.index("Язык и акценты")


def test_preview_markdown_contains_eyebrow_marker_with_mapping_label():
    """Concern 1 из отчёта Task 10: сырой markdown, который эта функция вставляет на целевую
    страницу, должен нести приватный маркер "<!-- video-eyebrow: <label> -->" непосредственно
    перед списком примеров — group_media_lists.py (следующий хук в пайплайне) читает его, чтобы
    выставить эйброу .video-block в название поля, а не в случайный ambient-заголовок целевой
    страницы. Маркер здесь — обычный текст в сыром markdown (ещё ДО прогона group_media_lists.py),
    так что он ожидаемо виден на этом этапе; то, что он вырезается из финального HTML — отдельно
    проверяется в test_group_media_lists.py::test_eyebrow_marker_sets_label_and_is_stripped_from_output."""
    target_md = (
        "### Темп речи\n\n"
        "Значения: Медленный / Быстрый.\n\n"
        "### Язык и акценты\n\n"
        "Значения: Русский / Английский / Другой.\n"
    )
    page = FakePage("manual-2-etap/04-classifier.md")
    result = on_page_markdown(target_md, page, None, None)
    assert "<!-- video-eyebrow: Темп речи -->" in result
    # маркер должен идти непосредственно перед списком примеров, не где попало
    assert result.index("<!-- video-eyebrow: Темп речи -->") < result.index("example1.mp4")


def _rakurs_test_mapping():
    """Синтетический mapping для регрессионных тестов ниже — раньше указывал на реальную запись
    MAPPINGS с source_heading="Ракурс", но эта запись удалена 18.08.2026 (превью "Ракурс" стало
    частью рукописного блока прямо в 04-classifier.md, поле больше не инжектируется отдельно).
    Сами регрессии (эйброу-маркер, пустая строка перед закрывающим </div>, взаимодействие с
    group_media_lists.py) по-прежнему актуальны для механизма в целом, поэтому мы держим их
    живыми через mapping, независимый от реального MAPPINGS — используем _apply_mapping()
    напрямую вместо on_page_markdown(), которая читает глобальный MAPPINGS."""
    return {
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "### Освещение",
        "position": "before_line",
        "source_file": "manual-2-etap/11-example-library.md",
        "source_heading": "Ракурс",
        "max_items": 2,
        "label": "Ракурс",
    }


def test_preview_markdown_eyebrow_marker_for_rakurs_mapping():
    from inject_example_previews import _apply_mapping

    mapping = _rakurs_test_mapping()
    target_md = (
        "### Преобладающий ракурс\n\n"
        "Значения: Анфас / Полуоборот (3/4) / Профиль. Решение «по наитию» допустимо.\n\n"
        "### Освещение\n\n"
        "Значения: Мягкое студийное / Естественное / Сложное.\n"
    )
    result = _apply_mapping(target_md, mapping)
    assert "<!-- video-eyebrow: Ракурс -->" in result


def test_mapping_with_hardcoded_items_skips_source_file():
    """Записи MAPPINGS с ключом "items" (видео зашиты прямо в коде, не читаются со страницы —
    см. запись "Тип речи", добавлено 20.08.2026 по просьбе пользователя убрать дублирующий
    раздел на странице "Банк примеров") не должны обращаться к DOCS_DIR/source_file вообще —
    иначе несуществующий source_file уронил бы сборку. max_items == len(items) гарантирует
    remaining == 0, так что "ещё N примеров" не появляется (ссылаться там уже некуда)."""
    from inject_example_previews import _apply_mapping

    mapping = {
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "### Освещение",
        "position": "before_line",
        "items": [
            "- **Пример А:** [видео](example1.mp4)",
            "- **Пример Б:** [видео](example2.mp4)",
        ],
        "max_items": 2,
        "label": "Проверка items",
    }
    target_md = "### Освещение\n\nЗначения: ...\n"
    result = _apply_mapping(target_md, mapping)
    assert "example1.mp4" in result
    assert "example2.mp4" in result
    assert "→ ещё" not in result
    assert "<!-- video-eyebrow: Проверка items -->" in result


def test_mapping_table_covers_expected_targets():
    targets = {m["target_file"] for m in MAPPINGS}
    assert "manual-2-etap/04-classifier.md" in targets
    assert "manual-3-etap/04-video-quality.md" in targets


def test_mapping_table_has_label_for_every_entry():
    """Concern 1 из отчёта Task 10: эйброу .video-block у инжектированных превью раньше
    наследовал случайный ambient-заголовок целевой страницы вместо названия поля. Каждая запись
    MAPPINGS должна явно нести короткий человекочитаемый label — источник правды для
    "<!-- video-eyebrow: ... -->" маркера, который _build_preview_markdown() эмитит для
    group_media_lists.py (см. test_group_media_lists.py::test_eyebrow_marker_*)."""
    expected_labels = {"Темп речи", "Эмоции", "Тип речи", "Битое", "Артефакт"}
    assert len(MAPPINGS) == len(expected_labels)
    labels = [mapping.get("label") for mapping in MAPPINGS]
    assert all(labels), "у каждой записи MAPPINGS должен быть непустой label"
    assert set(labels) == expected_labels


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
    from inject_example_previews import _apply_mapping

    mapping = _rakurs_test_mapping()
    target_md = (
        "### Преобладающий ракурс\n\n"
        "Значения: Анфас / Полуоборот (3/4) / Профиль. Решение «по наитию» допустимо.\n\n"
        "### Освещение\n\n"
        "Значения: Мягкое студийное / Естественное / Сложное.\n"
    )
    result = _apply_mapping(target_md, mapping)
    # remaining должен быть 0 для фикстуры "Ракурс" (ровно 2 примера = max_items)
    assert "→ ещё" not in result
    assert "\n\n</div>" in result, (
        "закрывающий </div> должен идти после пустой строки, а не сразу после "
        "последнего video-item"
    )


def test_more_link_anchor_matches_real_mkdocs_heading_id():
    """Регрессия: "→ ещё N прим." должна вести на якорь, который MkDocs реально проставит на
    заголовок раздела-источника. До этой правки inject_example_previews.py считал якорь своей
    отдельной (иначе написанной) функцией _slugify(), а site/mkdocs.yml вообще не задавал
    unicode-slugify для markdown_extensions.toc — из-за этого заголовки из чистой кириллицы
    («Темп речи», «Ракурс» и т.д., без единой латинской буквы/цифры) получали нечитаемый
    порядковый id "_N" вместо slug, и клик по ссылке никуда не долистывал (scrollY оставался 0,
    проверено вживую в Task 10). Теперь оба места используют одну и ту же
    pymdownx.slugs.slugify(case="lower") — здесь просто фиксируем, что она вообще выдаёт
    непустой, ожидаемо читаемый slug для целевых заголовков из MAPPINGS."""
    from inject_example_previews import MAPPINGS, _slugify_heading

    # Записи с "items" (видео зашиты прямо в MAPPINGS) не ссылаются ни на какой раздел-источник
    # ("ещё N примеров" для них не строится, см. комментарий в _build_preview_markdown), поэтому
    # у них нет "source_heading" и проверять здесь нечего.
    for mapping in MAPPINGS:
        if "source_heading" not in mapping:
            continue
        slug = _slugify_heading(mapping["source_heading"], "-")
        assert slug, f"пустой slug для {mapping['source_heading']!r} — снова получим id=\"_N\""
        assert slug == slug.lower()
        assert " " not in slug

    assert _slugify_heading("Темп речи", "-") == "темп-речи"


def test_injected_preview_survives_group_media_lists_without_broken_html():
    """Интеграционная регрессия на реальное взаимодействие двух хуков в порядке mkdocs.yml:
    inject_example_previews → (embed_local_media в реальном пайплайне превращает голые .mp4
    в <video>) → group_media_lists. Раньше на этой цепочке для превью "Ракурс" получался битый
    вложенный HTML `<div class="vi-cap"><span markdown="1"></div></span></div>`."""
    import embed_local_media
    import group_media_lists
    from inject_example_previews import _apply_mapping

    mapping = _rakurs_test_mapping()
    target_md = (
        "## Уточнения\n\n"
        "### Преобладающий ракурс\n\n"
        "Значения: Анфас / Полуоборот (3/4) / Профиль. Решение «по наитию» допустимо.\n\n"
        "### Освещение\n\n"
        "Значения: Мягкое студийное / Естественное / Сложное.\n"
    )
    page = FakePage(mapping["target_file"])
    md = _apply_mapping(target_md, mapping)
    md = embed_local_media.on_page_markdown(md, page, None, None)
    result = group_media_lists.on_page_markdown(md, page, None, None)

    assert "</div></span>" not in result, "битая вложенность vi-cap/span не должна встречаться"
    assert 'exampleA.mp4' in result
    assert 'exampleB.mp4' in result
    # Concern 1 из отчёта Task 10: эйброу теперь "Ракурс" (из label в MAPPINGS), а не случайный
    # заголовок целевой страницы ("Уточнения" из target_md выше) — и маркер-комментарий не
    # просочился в финальный HTML.
    assert '<span class="eyebrow">Ракурс</span>' in result
    assert "video-eyebrow" not in result

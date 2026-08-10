from build_compare_cards import on_page_markdown
from _render_helpers import render_html

TABLE_MD = (
    "Между сегментами должен быть зазор.\n\n"
    "| Правильно | Неправильно |\n"
    "|---|---|\n"
    "| ![Так правильно: два сегмента на таймлайне с зазором между ними]"
    "(assets/timeline-correct-spacing.png) | ![Так неправильно: два сегмента "
    "перекрываются, есть тёмная зона наложения](assets/timeline-incorrect-overlap.png) |\n"
    "| Между красным и зелёным сегментом есть промежуток | Красный и зелёный сегмент "
    "налезают друг на друга (тёмно-зелёная зона) |\n"
)

# Та же таблица, но с **bold**-разметкой в подписях — нужна для проверки, что markdown="1"
# реально работает (Fix 1 итогового обзора), а не просто присутствует в выводе как мёртвый
# атрибут.
TABLE_MD_WITH_BOLD_CAPTION = (
    "| Правильно | Неправильно |\n"
    "|---|---|\n"
    "| ![ок](assets/a.png) | ![плохо](assets/b.png) |\n"
    "| **Важно:** есть промежуток | **Важно:** зона наложения |\n"
)


def test_converts_table_to_compare_cards():
    result = on_page_markdown(TABLE_MD, None, None, None)
    assert '<div class="compare" markdown="1">' in result
    assert '<div class="compare-card good" markdown="1">' in result
    assert '<div class="compare-card bad" markdown="1">' in result
    # "../" — поправка на use_directory_urls, см. _path_utils.fix_local_asset_path: без неё
    # браузер запрашивает несуществующий .../02-segments/assets/... и картинка не грузится.
    assert 'src="../assets/timeline-correct-spacing.png"' in result
    assert 'src="../assets/timeline-incorrect-overlap.png"' in result
    assert "✓ Правильно" in result
    assert "✗ Неправильно" in result
    assert "Между красным и зелёным сегментом есть промежуток" in result
    assert "Красный и зелёный сегмент налезают друг на друга" in result
    assert "Между сегментами должен быть зазор." in result  # текст до таблицы сохранён


def test_table_without_images_untouched():
    md = "| Правильно | Неправильно |\n|---|---|\n| да | нет |\n"
    assert on_page_markdown(md, None, None, None) == md


def test_no_table_untouched():
    md = "Обычный текст без таблиц."
    assert on_page_markdown(md, None, None, None) == md


def test_rendered_html_has_no_leftover_markdown_1_or_literal_bold_markers():
    """Fix 1 итогового обзора: markdown="1" стоял только на внутреннем <span>, а не на всех
    div-предках (.compare/.compare-card/.compare-cap), и подпись шла в одну строку с окружающими
    тегами — markdown="1" был мёртвым атрибутом, **bold** утекал в вывод буквально. Проверяем
    через настоящий рендер (tests/_render_helpers.py), а не промежуточную строку хука."""
    result = on_page_markdown(TABLE_MD_WITH_BOLD_CAPTION, None, None, None)
    html = render_html(result)
    assert 'markdown="1"' not in html
    assert "**" not in html
    assert html.count("<strong>Важно:</strong>") == 2


def test_rendered_html_captions_preserved_alongside_images():
    result = on_page_markdown(TABLE_MD, None, None, None)
    html = render_html(result)
    assert 'src="../assets/timeline-correct-spacing.png"' in html
    assert "Между красным и зелёным сегментом есть промежуток" in html
    assert "Красный и зелёный сегмент налезают друг на друга" in html

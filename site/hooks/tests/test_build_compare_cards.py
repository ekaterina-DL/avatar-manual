from build_compare_cards import on_page_markdown

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


def test_converts_table_to_compare_cards():
    result = on_page_markdown(TABLE_MD, None, None, None)
    assert '<div class="compare">' in result
    assert '<div class="compare-card good">' in result
    assert '<div class="compare-card bad">' in result
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

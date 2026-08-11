from build_status_badges import on_page_markdown


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


PAGE = "manual-2-etap/09-disputed-points.md"


def test_resolved_becomes_green_badge():
    page = FakePage(PAGE)
    config = FakeConfig("/repo/avatar-manual-build/build")
    src = "- Статус: **Решено** — вариант A подтверждён напрямую.\n"
    result = on_page_markdown(src, page, config, None)
    assert '<span class="status-badge status-ok">🟢 Решено</span>' in result
    assert "— вариант A подтверждён напрямую." in result
    assert "**Решено**" not in result


def test_partial_becomes_yellow_badge():
    page = FakePage(PAGE)
    config = FakeConfig("/repo/avatar-manual-build/build")
    src = "- Статус: **Частично решено** — практика заказчика стабильна.\n"
    result = on_page_markdown(src, page, config, None)
    assert '<span class="status-badge status-partial">🟡 Частично решено</span>' in result
    assert "— практика заказчика стабильна." in result


def test_open_becomes_red_badge():
    page = FakePage(PAGE)
    config = FakeConfig("/repo/avatar-manual-build/build")
    src = "- Статус: **Не решено**, прямое противоречие.\n"
    result = on_page_markdown(src, page, config, None)
    assert '<span class="status-badge status-open">🔴 Не решено</span>' in result
    assert ", прямое противоречие." in result


def test_untouched_on_pdf_build():
    page = FakePage(PAGE)
    config = FakeConfig("/repo/avatar-manual-build/build-pdf")
    src = "- Статус: **Решено** — пояснение.\n"
    result = on_page_markdown(src, page, config, None)
    assert result == src


def test_untouched_on_unrelated_page():
    page = FakePage("manual-2-etap/02-segments.md")
    config = FakeConfig("/repo/avatar-manual-build/build")
    src = "- Статус: **Решено** — пояснение.\n"
    result = on_page_markdown(src, page, config, None)
    assert result == src


def test_ignores_status_word_not_at_start_of_bullet():
    """Вложенное упоминание "Статус:" в середине другого пункта (не в начале bullet-а) хук не
    трогает — реальный пример: пункт про максимальную длину видео содержит фразу
    "...прошли без замечаний. Статус: **не решено на уровне точной границы**, хотя..." внутри
    абзаца про 10:03/10:06, это не самостоятельная строка "- Статус: **...**"."""
    page = FakePage(PAGE)
    config = FakeConfig("/repo/avatar-manual-build/build")
    src = (
        "- ⚠️ Неясная точность порога. ...прошли без замечаний. Статус: **не решено на уровне "
        "точной границы**, хотя сам факт правила решён.\n"
    )
    result = on_page_markdown(src, page, config, None)
    assert result == src


def test_template_example_with_backticks_not_touched():
    page = FakePage(PAGE)
    config = FakeConfig("/repo/avatar-manual-build/build")
    src = "- Статус: `Решено` / `Частично решено` / `Не решено` — краткое пояснение (см. <файл>)\n"
    result = on_page_markdown(src, page, config, None)
    assert result == src


def test_badge_renders_inline_inside_list_item():
    from _render_helpers import render_html

    page = FakePage(PAGE)
    config = FakeConfig("/repo/avatar-manual-build/build")
    src = "- Статус: **Решено** — пояснение.\n"
    markdown_out = on_page_markdown(src, page, config, None)
    html = render_html(markdown_out)
    assert '<li>' in html
    assert '<span class="status-badge status-ok">🟢 Решено</span>' in html

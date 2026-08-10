from build_dispute_flow import on_page_markdown
from _render_helpers import render_html

SECTION_MD = (
    "### Как устроено оспаривание ошибки (механика апелляций)\n\n"
    "Если асессор не согласен с конкретной ошибкой в ОС, процесс идёт в три шага:\n"
    "1. Асессор смотрит эксель-таблицу с разбором ошибок; если с чем-то не согласен — пишет в\n"
    "   специальный тред (внутри команды Data Light).\n"
    "2. Data Light рассматривает обращение и либо соглашается с исходным ответом валидатора\n"
    "   (бракует апелляцию), либо одобряет её и отправляет вопрос на уточнение заказчику.\n"
    "3. Заказчик либо соглашается (ошибка будет исправлена в их системе), либо нет.\n\n"
    "Важный нюанс: повторную выгрузку уже отправленных данных не делают.\n"
)


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


def test_replaces_numbered_list_with_flow_diagram_on_site_build():
    page = FakePage("manual-2-etap/00-overview.md")
    config = FakeConfig("/repo/avatar-manual-build/build")
    result = on_page_markdown(SECTION_MD, page, config, None)
    assert '<div class="apeal-flow">' in result
    assert result.count('<div class="apeal-step">') == 3
    assert "1. Асессор смотрит эксель-таблицу" not in result
    # интро-предложение и абзац после списка остаются нетронутыми
    assert "Если асессор не согласен с конкретной ошибкой в ОС, процесс идёт в три шага:" in result
    assert "Важный нюанс: повторную выгрузку уже отправленных данных не делают." in result


def test_untouched_on_pdf_build():
    page = FakePage("manual-2-etap/00-overview.md")
    config = FakeConfig("/repo/avatar-manual-build/build-pdf")
    result = on_page_markdown(SECTION_MD, page, config, None)
    assert result == SECTION_MD


def test_untouched_on_unrelated_page():
    page = FakePage("manual-3-etap/00-overview.md")
    config = FakeConfig("/repo/avatar-manual-build/build")
    result = on_page_markdown(SECTION_MD, page, config, None)
    assert result == SECTION_MD


def test_noop_if_source_list_already_changed():
    page = FakePage("manual-2-etap/00-overview.md")
    config = FakeConfig("/repo/avatar-manual-build/build")
    changed = "### Как устроено оспаривание ошибки\n\nСовсем другой текст.\n"
    result = on_page_markdown(changed, page, config, None)
    assert result == changed


def test_diagram_renders_as_html_block_not_swallowed_into_paragraph():
    page = FakePage("manual-2-etap/00-overview.md")
    config = FakeConfig("/repo/avatar-manual-build/build")
    markdown_out = on_page_markdown(SECTION_MD, page, config, None)
    html = render_html(markdown_out)
    assert '<div class="apeal-flow">' in html
    # div не должен оказаться внутри <p> — иначе браузер молча разорвёт разметку
    assert "<p>" + '<div class="apeal-flow">' not in html.replace("\n", "")

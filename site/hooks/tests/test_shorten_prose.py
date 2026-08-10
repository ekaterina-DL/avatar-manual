from shorten_prose import on_page_markdown

VALIDATOR_SECTION = (
    "### Валидатор тоже может ошибаться\n\n"
    "Обратная связь (ОС) от валидатора — это не абсолютная истина. Каждую отмеченную в ОС ошибку\n"
    "стоит внимательно перечитывать и сверять с тем, что реально происходит на видео: если ваша\n"
    "разметка кажется вам явно верной, а комментарий валидатора — нет, **не соглашайтесь\n"
    "автоматически** — аргументированно переспрашивайте и, если нужно, оспаривайте (как именно —\n"
    "см. ниже). Заказчик рассматривает такие обращения и при необходимости поправляет валидатора, а\n"
    "не автоматически встаёт на его сторону. Подтверждённые реальные случаи: заказчик встал на\n"
    "сторону оператора против нового валидатора ([07-faq.md](07-faq.md#можно-ли-оспорить-решение-валидатора-да--и-заказчик-может-встать-на-сторону-оператора));\n"
    "на 3 этапе эталонный ханипот был задним числом скорректирован после обоснованного возражения\n"
    "исполнителя (см. [мануал 3 этапа](../manual-3-etap/05-faq.md)).\n\n"
    "### Как устроено оспаривание ошибки\n"
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


SITE_CONFIG = FakeConfig("/repo/avatar-manual-build/build")
PDF_CONFIG = FakeConfig("/repo/avatar-manual-build/build-pdf")


def test_shortens_validator_section_and_drops_confirmed_cases():
    page = FakePage("manual-2-etap/00-overview.md")
    result = on_page_markdown(VALIDATOR_SECTION, page, SITE_CONFIG, None)
    assert "Подтверждённые реальные случаи" not in result
    assert "эталонный ханипот" not in result
    assert "может поправить валидатора — не всегда встаёт на его сторону." in result


def test_keeps_surrounding_headings():
    page = FakePage("manual-2-etap/00-overview.md")
    result = on_page_markdown(VALIDATOR_SECTION, page, SITE_CONFIG, None)
    assert "### Валидатор тоже может ошибаться" in result
    assert "### Как устроено оспаривание ошибки" in result


def test_untouched_on_pdf_build():
    page = FakePage("manual-2-etap/00-overview.md")
    result = on_page_markdown(VALIDATOR_SECTION, page, PDF_CONFIG, None)
    assert result == VALIDATOR_SECTION


def test_untouched_on_other_pages():
    page = FakePage("manual-3-etap/00-overview.md")
    result = on_page_markdown(VALIDATOR_SECTION, page, SITE_CONFIG, None)
    assert result == VALIDATOR_SECTION


def test_noop_if_source_text_already_changed():
    page = FakePage("manual-2-etap/00-overview.md")
    changed = "### Валидатор тоже может ошибаться\n\nСовсем другой текст.\n"
    result = on_page_markdown(changed, page, SITE_CONFIG, None)
    assert result == changed

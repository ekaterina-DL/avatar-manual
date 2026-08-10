import re

from _build_profile import is_pdf_build

# Точное соответствие исходному тексту 3 пунктов раздела "Как устроено оспаривание ошибки"
# (manual-2-etap/00-overview.md) — без нечёткого сопоставления. Если исходный текст изменится,
# regex просто не совпадёт и хук ничего не сделает (на сайте останется исходный список).
_LIST_RE = re.compile(
    r"1\. Асессор смотрит эксель-таблицу.*?\n"
    r"2\. Data Light рассматривает обращение.*?\n"
    r"3\. Заказчик либо соглашается.*?\n",
    re.S,
)

_DIAGRAM = (
    '<div class="apeal-flow">\n'
    '<div class="apeal-step">\n'
    '<span class="apeal-num">1</span><span class="apeal-title">Асессор</span>\n'
    "<p>не согласен с ОС → пишет в тред команды Data Light</p>\n"
    "</div>\n"
    '<div class="apeal-arrow">→</div>\n'
    '<div class="apeal-step">\n'
    '<span class="apeal-num">2</span><span class="apeal-title">Data Light</span>\n'
    "<p>рассматривает обращение → бракует апелляцию или передаёт заказчику</p>\n"
    "</div>\n"
    '<div class="apeal-arrow">→</div>\n'
    '<div class="apeal-step">\n'
    '<span class="apeal-num">3</span><span class="apeal-title">Заказчик</span>\n'
    "<p>подтверждает (ошибку исправят) или нет</p>\n"
    "</div>\n"
    "</div>"
)


def on_page_markdown(markdown, page, config, files):
    """Нумерованный список из раздела "Как устроено оспаривание ошибки" (manual-2-etap/00-overview.md)
    заменяет на компактную горизонтальную схему из 3 шагов — на сайте длинный список читался
    громоздко. Вступительное предложение перед списком и абзац "Важный нюанс" после — не трогает,
    заменяется только сам список. PDF-профиль не трогаем: он задуман как полный документ,
    список остаётся текстом в исходном виде."""
    if is_pdf_build(config):
        return markdown
    if page.file.src_uri.replace("\\", "/") != "manual-2-etap/00-overview.md":
        return markdown
    return _LIST_RE.sub("\n" + _DIAGRAM + "\n", markdown, count=1)

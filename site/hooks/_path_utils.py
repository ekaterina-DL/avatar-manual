import re

_EXTERNAL_RE = re.compile(r'^(?:https?:)?//|^[a-z][a-z0-9+.-]*:', re.IGNORECASE)


def fix_local_asset_path(src):
    """Хуки, которые превращают markdown-ссылку/картинку в СЫРОЙ HTML (build_compare_cards.py →
    <img>, embed_local_media.py → <video><source>), переносят relative-путь из исходника
    буквально ("assets/foo.png"). Это верно относительно самого .md-файла
    (manual-2-etap/02-segments.md лежит рядом с manual-2-etap/assets/), но НЕ относительно
    собранной HTML-страницы: из-за use_directory_urls каждая страница мануала собирается на
    уровень глубже (manual-2-etap/02-segments.md → manual-2-etap/02-segments/index.html), а
    ассеты остаются на исходном месте (manual-2-etap/assets/...). Markdown-синтаксис ![]()/[]()
    MkDocs сам relativизирует под эту вложенность на этапе рендера; сырой HTML, вставленный
    хуком в текст ДО рендера, — нет, он проходит мимо этого механизма. Без поправки браузер
    запрашивает несуществующий manual-2-etap/02-segments/assets/foo.png вместо верного
    manual-2-etap/assets/foo.png — картинка/видео молча не загружается (найдено вживую в
    Task 10 QA: карточки "Правильно/Неправильно" на 02-segments.md показывали битую иконку).

    Внешние URL (http/https/vk.com/...) и уже поднятые на уровень выше пути ("../...") не трогаем
    — единственный паттерн, который реально требует поправки во всём мануале на сегодня, это
    локальные "assets/<файл>" (проверено: ни один .md-файл мануала не кладёт такие ассеты глубже
    одного уровня и не ссылается на чужую assets/ другого этапа)."""
    if _EXTERNAL_RE.match(src) or src.startswith("../") or src.startswith("/"):
        return src
    if src.startswith("assets/"):
        return "../" + src
    return src

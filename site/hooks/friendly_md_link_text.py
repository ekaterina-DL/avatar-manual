import re

# Точное соответствие (файл -> заголовок в nav сайта, site/mkdocs.yml -> nav). Без нечёткого
# сопоставления — тот же принцип, что и в hide_site_only_sections.py.
TITLES = {
    "manual-2-etap/00-overview.md": "Обзор проекта",
    "manual-2-etap/01-general-requirements.md": "Общие требования к видео и аудио",
    "manual-2-etap/02-segments.md": "Сегменты",
    "manual-2-etap/04-classifier.md": "Классификатор",
    "manual-2-etap/05-what-to-label.md": "Что размечаем",
    "manual-2-etap/06-common-mistakes.md": "Частые ошибки",
    "manual-2-etap/11-example-library.md": "Банк примеров",
    "manual-3-etap/00-overview.md": "Обзор проекта",
    "manual-3-etap/01-classifier.md": "Классификатор",
    "manual-3-etap/02-open-questions.md": "Открытые вопросы",
    "manual-3-etap/03-common-mistakes.md": "Частые ошибки",
    "manual-3-etap/04-video-quality.md": "Критерии качества",
    "manual-3-etap/05-faq.md": "Разбор кейсов (FAQ)",
    "manual-3-etap/06-general-requirements.md": "Общие правила",
    "manual-3-etap/07-example-library.md": "Банк примеров",
}

STAGE_LABEL = {
    "manual-2-etap": "2 этап",
    "manual-3-etap": "3 этап",
}

# Текст ссылки НАЧИНАЕТСЯ с имени файла мануала: "00-overview.md", "../manual-3-etap/00-overview.md",
# с необязательным #якорем и, изредка, добавленными вручную словами после (например
# "00-overview.md 2 этапа" в manual-3-etap/00-overview.md) — весь текст в этом случае заменяется
# целиком на название раздела (плюс автоматическая пометка этапа, если ссылка ведёт в другую
# папку — см. STAGE_LABEL ниже), чтобы не задваивать пометку этапа. Сам якорь из видимого текста
# выбрасываем — ссылка (href) при этом не меняется, переход по ней работает как раньше.
#
# Группа 2/3 — редкий случай, когда пометка этапа дописана автором СНАРУЖИ скобок, сразу после
# ссылки ("[00-overview.md](...) 2 этапа" в manual-3-etap/00-overview.md): без этой группы
# получилось бы задвоение "Обзор проекта (2 этап) 2 этапа" — свою пометку мы уже добавляем сами.
_LINK_RE = re.compile(
    r"\[(?:\.\./)?(?:manual-[23]-etap/)?\d{2}-[a-z0-9-]+\.md(?:#[^\]]*)?[^\]]*\]\(([^)]+)\)"
    r"(\s+([23])\s*этап[а-я]*)?"
)


def on_page_markdown(markdown, page, config, files):
    """Ссылки, где видимый текст — это буквально имя .md-файла ("11-example-library.md",
    "00-overview.md#..."), заменяет на понятное название раздела сайта (из TITLES), не трогая
    сам href — переход по ссылке ведёт туда же, куда и раньше. Целевой файл определяется по href
    (а не по тексту ссылки), потому что часть ссылок в мануале написана без manual-N-etap/
    префикса в тексте, полагаясь только на относительный путь в href. Ссылки на файлы, которых
    нет в TITLES (например, исключённые из сборки _sources-log.md — их дальше нейтрализует
    neutralize_excluded_links.py), не трогает."""
    current_folder = page.file.src_uri.replace("\\", "/").split("/")[0]

    def repl(match):
        href = match.group(1)
        trailing, trailing_digit = match.group(2), match.group(3)
        href_path = href.split("#", 1)[0].replace("\\", "/")
        if href_path.startswith("../"):
            norm = href_path[3:]
        elif "/" in href_path:
            norm = href_path
        else:
            norm = f"{current_folder}/{href_path}"
        title = TITLES.get(norm)
        if title is None:
            return match.group(0)
        target_folder = norm.split("/")[0]
        target_stage_digit = target_folder.split("-")[1] if "-" in target_folder else None
        if target_folder != current_folder:
            title = f"{title} ({STAGE_LABEL.get(target_folder, target_folder)})"
            if trailing_digit == target_stage_digit:
                trailing = None
        result = f"[{title}]({href})"
        return result + trailing if trailing else result

    return _LINK_RE.sub(repl, markdown)

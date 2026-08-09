import re

from _path_utils import fix_local_asset_path

# [текст](путь-или-url.mp4) — ровно markdown-ссылка, ведущая на файл с расширением .mp4
BRACKETED_MP4_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+\.mp4)\)")

# Голая ссылка на .mp4, без markdown-скобок — например, в 07-example-library.md (3 этап).
# Отрицательный lookbehind на " и ( — чтобы не задеть src="..." внутри уже вставленного
# <source> (эта регулярка выполняется вторым проходом, после BRACKETED_MP4_RE) и ссылки,
# которые всё-таки были в скобках, но синтаксис которых не подошёл под первую регулярку.
BARE_MP4_RE = re.compile(r'(?<!["(])(https?://\S+?\.mp4)(?!\S)')

# Длинные обучающие видео (скачаны локально под этим префиксом) — по дизайну должны
# оставаться кликабельными ссылками, а не превращаться в плеер. См. site/PLAN.md:
# "4 длинных обучающих видео остаются кликабельными ссылками, не встраиваются плеером".
LONG_TRAINING_VIDEO_PREFIX = "training-"


def _video_tag(src, alt_text=""):
    filename = src.rsplit("/", 1)[-1]
    if filename.startswith(LONG_TRAINING_VIDEO_PREFIX):
        return None
    src = fix_local_asset_path(src)
    return (
        f'<video controls preload="metadata" style="max-width:100%">'
        f'<source src="{src}" type="video/mp4">'
        f'{alt_text}</video>'
    )


def on_page_markdown(markdown, page, config, files):
    """Превращает ссылки на .mp4 (локальные assets/ или внешние sbercloud), как markdown-ссылки
    [текст](url), так и голые url в тексте, во встроенный HTML5-плеер. Не трогает: (1) ссылки,
    не оканчивающиеся на .mp4 (например, все disk.yandex.ru/i/... — это share-страницы, а не
    прямые файлы); (2) локальные файлы с именем на training- (длинные обучающие видео) — они
    остаются обычными кликабельными ссылками, как и задумано в дизайне.
    """

    def replace_bracketed(match):
        alt_text, src = match.group(1), match.group(2)
        tag = _video_tag(src, alt_text)
        return tag if tag is not None else match.group(0)

    markdown = BRACKETED_MP4_RE.sub(replace_bracketed, markdown)

    def replace_bare(match):
        src = match.group(1)
        tag = _video_tag(src)
        return tag if tag is not None else match.group(0)

    return BARE_MP4_RE.sub(replace_bare, markdown)

import re

# [текст](путь-или-url.mp4) — ровно markdown-ссылка, ведущая на файл с расширением .mp4
MP4_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+\.mp4)\)")

# Длинные обучающие видео (скачаны локально под этим префиксом) — по дизайну должны
# оставаться кликабельными ссылками, а не превращаться в плеер. См. site/PLAN.md:
# "4 длинных обучающих видео остаются кликабельными ссылками, не встраиваются плеером".
LONG_TRAINING_VIDEO_PREFIX = "training-"


def on_page_markdown(markdown, page, config, files):
    """Превращает markdown-ссылки на .mp4 (локальные assets/ или внешние sbercloud)
    во встроенный HTML5-плеер. Не трогает: (1) ссылки, не оканчивающиеся на .mp4
    (например, все disk.yandex.ru/i/... — это share-страницы, а не прямые файлы);
    (2) локальные файлы с именем на training- (длинные обучающие видео) — они
    остаются обычными кликабельными ссылками, как и задумано в дизайне.
    """
    def replace(match):
        alt_text, src = match.group(1), match.group(2)
        filename = src.rsplit("/", 1)[-1]
        if filename.startswith(LONG_TRAINING_VIDEO_PREFIX):
            return match.group(0)
        return (
            f'<video controls preload="metadata" style="max-width:100%">'
            f'<source src="{src}" type="video/mp4">'
            f'{alt_text}</video>'
        )

    return MP4_LINK_RE.sub(replace, markdown)

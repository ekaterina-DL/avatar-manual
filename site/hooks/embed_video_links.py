import re

from _build_profile import is_pdf_build


def _vk_iframe(oid, video_id):
    return (
        f'<iframe class="embedded-video" '
        f'src="https://vk.com/video_ext.php?oid={oid}&id={video_id}&hd=2" '
        f'loading="lazy" allowfullscreen></iframe>'
    )


def _youtube_iframe(video_id):
    # youtube-nocookie.com (режим «расширенной защиты конфиденциальности») вместо youtube.com —
    # обычный домен youtube.com для встраивания в некоторых браузерах блокируется защитой от
    # трекеров (Brave Shields, Firefox ETP, Safari ITP и т.п.), из-за чего плеер вместо
    # проигрывания на месте откатывается к ссылке «Watch on YouTube», открывающей видео в новой
    # вкладке — привязанный к видео cookie до взаимодействия с плеером не выставляется, что реже
    # триггерит такую блокировку.
    return (
        f'<iframe class="embedded-video" '
        f'src="https://www.youtube-nocookie.com/embed/{video_id}" '
        f'loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
        f'gyroscope; picture-in-picture" allowfullscreen></iframe>'
    )


def _captioned(iframe_html, caption):
    """Оборачивает iframe в <figure> с видимой подписью — используется ТОЛЬКО для markdown-ссылок
    вида [подпись](url): голая ссылка подписи не имеет вовсе, оборачивать её незачем (см. Fix 2
    итогового обзора). Подпись — обычно короткий id видео ("FqnaRHnTwck"), не markdown-разметка,
    поэтому <figcaption> не помечен markdown="1" (в остальных карточках на сайте подпись — тоже
    просто текст лейбла, ср. .vi-cap/.compare-cap)."""
    return f'<figure class="embedded-video-figure">{iframe_html}<figcaption>{caption}</figcaption></figure>'


VK_BRACKETED_RE = re.compile(r'\[([^\]]*)\]\(https?://vkvideo\.ru/video(-?\d+)_(\d+)(?:\?\S*)?\)')
VK_BARE_RE = re.compile(r'(?<!["(])https?://vkvideo\.ru/video(-?\d+)_(\d+)(?:\?\S*)?')
YOUTUBE_BRACKETED_RE = re.compile(
    r'\[([^\]]*)\]\(https?://(?:www\.)?youtube\.com/shorts/([A-Za-z0-9_-]+)\)'
)
YOUTUBE_BARE_RE = re.compile(r'(?<!["(])https?://(?:www\.)?youtube\.com/shorts/([A-Za-z0-9_-]+)')
# Обычная (не /shorts/) ссылка на YouTube-видео, напр. ".../watch?v=g2IF5NG2vU4" — те же два
# прохода (сначала markdown-ссылки, потом голые), тот же формат embed-плеера, что и у /shorts/.
YOUTUBE_WATCH_BRACKETED_RE = re.compile(
    r'\[([^\]]*)\]\(https?://(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]+)(?:&\S*)?\)'
)
YOUTUBE_WATCH_BARE_RE = re.compile(
    r'(?<!["(])https?://(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]+)(?:&\S*)?'
)


def _replace_vk_bracketed(match):
    caption, oid, video_id = match.groups()
    return _captioned(_vk_iframe(oid, video_id), caption)


def _replace_youtube_bracketed(match):
    caption, video_id = match.groups()
    return _captioned(_youtube_iframe(video_id), caption)


def on_page_markdown(markdown, page, config, files):
    """Превращает ссылки на vkvideo.ru и youtube.com (и /shorts/, и обычные /watch?v=) во
    встроенный iframe-плеер —
    и голые ссылки (без подписи, просто плеер), и markdown-ссылки вида [текст](url) (плеер +
    видимая подпись <figcaption> с исходным текстом ссылки, см. Fix 2 итогового обзора — раньше
    подпись отбрасывалась целиком, что ломало визуальную согласованность списков, где соседние
    пункты подписаны id видео, напр. manual-2-etap/05-what-to-label.md:72). loading="lazy" —
    нативная отложенная загрузка браузера, без JS. Двухпроходная схема (сначала markdown-ссылки,
    потом голые) не даёт голому проходу задеть URL внутри src="..." уже вставленного iframe —
    см. тот же приём в embed_local_media.py.

    PDF-профиль — исключение (Fix 3 итогового обзора, человек решил): в печатной версии iframe
    нельзя кликнуть и постер не показывается (живая проверка в Task 10) — 11+ пустых плеерных
    боксов без единого способа опознать видео. Восстанавливаем ДОСАЙТОВОЕ поведение: hook —
    no-op, PDF получает исходный markdown (картинка-кадр + подпись + обычная кликабельная
    ссылка/URL как текст, без plugins)."""
    if is_pdf_build(config):
        return markdown
    markdown = VK_BRACKETED_RE.sub(_replace_vk_bracketed, markdown)
    markdown = VK_BARE_RE.sub(lambda m: _vk_iframe(*m.groups()), markdown)
    markdown = YOUTUBE_BRACKETED_RE.sub(_replace_youtube_bracketed, markdown)
    markdown = YOUTUBE_BARE_RE.sub(lambda m: _youtube_iframe(*m.groups()), markdown)
    markdown = YOUTUBE_WATCH_BRACKETED_RE.sub(_replace_youtube_bracketed, markdown)
    markdown = YOUTUBE_WATCH_BARE_RE.sub(lambda m: _youtube_iframe(*m.groups()), markdown)
    return markdown

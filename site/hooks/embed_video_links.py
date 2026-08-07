import re


def _vk_iframe(oid, video_id):
    return (
        f'<iframe class="embedded-video" '
        f'src="https://vk.com/video_ext.php?oid={oid}&id={video_id}&hd=2" '
        f'loading="lazy" allowfullscreen></iframe>'
    )


def _youtube_iframe(video_id):
    return (
        f'<iframe class="embedded-video" '
        f'src="https://www.youtube.com/embed/{video_id}" '
        f'loading="lazy" allowfullscreen></iframe>'
    )


VK_BRACKETED_RE = re.compile(r'\[[^\]]*\]\(https?://vkvideo\.ru/video(-?\d+)_(\d+)(?:\?\S*)?\)')
VK_BARE_RE = re.compile(r'(?<!["(])https?://vkvideo\.ru/video(-?\d+)_(\d+)(?:\?\S*)?')
YOUTUBE_BRACKETED_RE = re.compile(
    r'\[[^\]]*\]\(https?://(?:www\.)?youtube\.com/shorts/([A-Za-z0-9_-]+)\)'
)
YOUTUBE_BARE_RE = re.compile(r'(?<!["(])https?://(?:www\.)?youtube\.com/shorts/([A-Za-z0-9_-]+)')


def on_page_markdown(markdown, page, config, files):
    """Превращает ссылки на vkvideo.ru и youtube.com/shorts во встроенный iframe-плеер —
    и голые ссылки, и markdown-ссылки вида [текст](url) (тогда подпись отбрасывается, весь
    markdown-линк целиком заменяется на плеер). loading="lazy" — нативная отложенная загрузка
    браузера, без JS. Двухпроходная схема (сначала markdown-ссылки, потом голые) не даёт голому
    проходу задеть URL внутри src="..." уже вставленного iframe — см. тот же приём в
    embed_local_media.py."""
    markdown = VK_BRACKETED_RE.sub(lambda m: _vk_iframe(*m.groups()), markdown)
    markdown = VK_BARE_RE.sub(lambda m: _vk_iframe(*m.groups()), markdown)
    markdown = YOUTUBE_BRACKETED_RE.sub(lambda m: _youtube_iframe(*m.groups()), markdown)
    markdown = YOUTUBE_BARE_RE.sub(lambda m: _youtube_iframe(*m.groups()), markdown)
    return markdown

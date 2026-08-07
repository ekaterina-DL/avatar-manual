import re

VK_RE = re.compile(r'https?://vkvideo\.ru/video(-?\d+)_(\d+)(?:\?\S*)?')
YOUTUBE_SHORTS_RE = re.compile(r'https?://(?:www\.)?youtube\.com/shorts/([A-Za-z0-9_-]+)')


def _embed_vk(match):
    oid, video_id = match.group(1), match.group(2)
    return (
        f'<iframe class="embedded-video" '
        f'src="https://vk.com/video_ext.php?oid={oid}&id={video_id}&hd=2" '
        f'loading="lazy" allowfullscreen></iframe>'
    )


def _embed_youtube(match):
    video_id = match.group(1)
    return (
        f'<iframe class="embedded-video" '
        f'src="https://www.youtube.com/embed/{video_id}" '
        f'loading="lazy" allowfullscreen></iframe>'
    )


def on_page_markdown(markdown, page, config, files):
    """Превращает голые ссылки на vkvideo.ru и youtube.com/shorts во встроенный iframe-плеер.
    loading="lazy" — нативная отложенная загрузка браузера, без JS."""
    markdown = VK_RE.sub(_embed_vk, markdown)
    markdown = YOUTUBE_SHORTS_RE.sub(_embed_youtube, markdown)
    return markdown

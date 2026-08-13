from embed_video_links import on_page_markdown


class FakeSiteDir:
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return self._value


class FakeConfig(dict):
    def __init__(self, site_dir):
        super().__init__()
        self.site_dir = FakeSiteDir(site_dir)


# Хук теперь читает config.site_dir (Fix 3 итогового обзора: no-op на PDF-профиле) — все
# существующие тесты сайта используют не-PDF site_dir, чтобы явно проверять поведение САЙТА.
SITE_CONFIG = FakeConfig("/repo/avatar-manual-build/build")
PDF_CONFIG = FakeConfig("/repo/avatar-manual-build/build-pdf")


def test_vk_link_with_positive_owner():
    md = "**Пример 1:** https://vkvideo.ru/video712360465_456239217"
    result = on_page_markdown(md, None, SITE_CONFIG, None)
    assert (
        '<iframe class="embedded-video" '
        'src="https://vk.com/video_ext.php?oid=712360465&id=456239217&hd=2" '
        'loading="lazy" allowfullscreen></iframe>'
    ) in result


def test_vk_link_with_negative_owner():
    md = "**Пример 2:** https://vkvideo.ru/video-45280055_456240146"
    result = on_page_markdown(md, None, SITE_CONFIG, None)
    assert "oid=-45280055&id=456240146" in result


def test_vk_link_with_query_string_is_stripped():
    md = "**Пример 4:** https://vkvideo.ru/video-102814524_456240009?list=ln-6LGJHsXLGhcRMCXpnl"
    result = on_page_markdown(md, None, SITE_CONFIG, None)
    assert "oid=-102814524&id=456240009" in result
    assert "list=" not in result


YOUTUBE_ALLOW = (
    'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; '
    'picture-in-picture"'
)


def test_youtube_shorts_link():
    md = "**Антипример 1:** https://www.youtube.com/shorts/kLTpStNQRF0"
    result = on_page_markdown(md, None, SITE_CONFIG, None)
    assert (
        '<iframe class="embedded-video" '
        'src="https://www.youtube-nocookie.com/embed/kLTpStNQRF0" '
        f'loading="lazy" {YOUTUBE_ALLOW} allowfullscreen></iframe>'
    ) in result


def test_youtube_watch_link():
    md = "**Пример:** https://www.youtube.com/watch?v=g2IF5NG2vU4"
    result = on_page_markdown(md, None, SITE_CONFIG, None)
    assert (
        '<iframe class="embedded-video" '
        'src="https://www.youtube-nocookie.com/embed/g2IF5NG2vU4" '
        f'loading="lazy" {YOUTUBE_ALLOW} allowfullscreen></iframe>'
    ) in result


def test_youtube_watch_link_inside_markdown_link():
    md = "- [g2IF5NG2vU4](https://www.youtube.com/watch?v=g2IF5NG2vU4) (с 35 секунды) — подходит."
    result = on_page_markdown(md, None, SITE_CONFIG, None)
    assert (
        '<iframe class="embedded-video" '
        'src="https://www.youtube-nocookie.com/embed/g2IF5NG2vU4" '
        f'loading="lazy" {YOUTUBE_ALLOW} allowfullscreen></iframe>'
    ) in result
    assert '<figcaption>g2IF5NG2vU4</figcaption>' in result
    assert "(с 35 секунды) — подходит." in result


def test_unrelated_text_untouched():
    md = "Обычный текст без ссылок на видео."
    assert on_page_markdown(md, None, SITE_CONFIG, None) == md


def test_youtube_shorts_inside_markdown_link():
    """Fix 2 итогового обзора (человек решил): подпись markdown-ссылки ([FqnaRHnTwck](url))
    больше не отбрасывается целиком, а сохраняется видимой под плеером в <figcaption> — раньше
    неотличимость от голой ссылки ломала консистентность списков, где соседние пункты подписаны
    id видео (см. manual-2-etap/05-what-to-label.md:72). Сломанный артефакт "](<iframe" (то, что
    чинил исходный Task 3 фикс — markdown-ссылка не должна ломаться на "](" + iframe) всё ещё не
    должен появляться."""
    md = "- ❌ [FqnaRHnTwck](https://www.youtube.com/shorts/FqnaRHnTwck) — не подходит."
    result = on_page_markdown(md, None, SITE_CONFIG, None)
    assert (
        '<iframe class="embedded-video" '
        'src="https://www.youtube-nocookie.com/embed/FqnaRHnTwck" '
        f'loading="lazy" {YOUTUBE_ALLOW} allowfullscreen></iframe>'
    ) in result
    assert '<figcaption>FqnaRHnTwck</figcaption>' in result
    assert '<figure class="embedded-video-figure">' in result
    assert "](<iframe" not in result


def test_vk_link_inside_markdown_link():
    """См. test_youtube_shorts_inside_markdown_link — то же самое решение (Fix 2), но для VK."""
    md = "[смотреть](https://vkvideo.ru/video712360465_456239217)"
    result = on_page_markdown(md, None, SITE_CONFIG, None)
    assert "oid=712360465&id=456239217" in result
    assert '<figcaption>смотреть</figcaption>' in result
    assert '<figure class="embedded-video-figure">' in result


def test_bare_link_has_no_caption_or_figure_wrapper():
    """Голая (не markdown-) ссылка не имеет подписи вовсе — оборачивать её в <figure> незачем,
    остаётся просто iframe (не изменилось этим фиксом, но явно фиксируется тестом, раз соседний
    markdown-ссылочный случай теперь отличается по разметке)."""
    md = "**Пример 1:** https://vkvideo.ru/video712360465_456239217"
    result = on_page_markdown(md, None, SITE_CONFIG, None)
    assert "<figure" not in result
    assert "<figcaption" not in result


def test_real_line_05_what_to_label_keeps_caption_and_surrounding_text():
    """Реальная строка manual-2-etap/05-what-to-label.md:72 — подпись FqnaRHnTwck должна выжить
    вместе с плеером, а окружающий текст абзаца (до и после ссылки) остаться нетронутым."""
    md = (
        "  - ❌ [FqnaRHnTwck](https://www.youtube.com/shorts/FqnaRHnTwck) — не подходит сразу по двум\n"
        "    причинам: это генерация нейросети (исключаем в принципе, см. ниже) и вдобавок липсинк/\n"
        "    артикуляция персонажа тоже не подходит.\n"
    )
    result = on_page_markdown(md, None, SITE_CONFIG, None)
    assert (
        '<iframe class="embedded-video" '
        'src="https://www.youtube-nocookie.com/embed/FqnaRHnTwck" '
        f'loading="lazy" {YOUTUBE_ALLOW} allowfullscreen></iframe>'
    ) in result
    assert '<figcaption>FqnaRHnTwck</figcaption>' in result
    assert "  - ❌ " in result
    assert "— не подходит сразу по двум" in result
    assert "причинам: это генерация нейросети (исключаем в принципе, см. ниже) и вдобавок липсинк/" in result
    assert "артикуляция персонажа тоже не подходит." in result


def test_noop_on_pdf_build():
    """Fix 3 итогового обзора (человек решил): на PDF-профиле хук — полный no-op, восстанавливает
    досайтовое поведение (кадр-картинка + подпись + кликабельная ссылка как обычный markdown),
    потому что iframe в печати нельзя кликнуть и постер не показывается."""
    md = (
        "**Пример 1:** https://vkvideo.ru/video712360465_456239217\n"
        "- ❌ [FqnaRHnTwck](https://www.youtube.com/shorts/FqnaRHnTwck) — не подходит.\n"
    )
    result = on_page_markdown(md, None, PDF_CONFIG, None)
    assert result == md
    assert "<iframe" not in result
    assert "<figure" not in result

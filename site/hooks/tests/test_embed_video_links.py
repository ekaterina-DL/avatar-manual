from embed_video_links import on_page_markdown


def test_vk_link_with_positive_owner():
    md = "**Пример 1:** https://vkvideo.ru/video712360465_456239217"
    result = on_page_markdown(md, None, None, None)
    assert (
        '<iframe class="embedded-video" '
        'src="https://vk.com/video_ext.php?oid=712360465&id=456239217&hd=2" '
        'loading="lazy" allowfullscreen></iframe>'
    ) in result


def test_vk_link_with_negative_owner():
    md = "**Пример 2:** https://vkvideo.ru/video-45280055_456240146"
    result = on_page_markdown(md, None, None, None)
    assert "oid=-45280055&id=456240146" in result


def test_vk_link_with_query_string_is_stripped():
    md = "**Пример 4:** https://vkvideo.ru/video-102814524_456240009?list=ln-6LGJHsXLGhcRMCXpnl"
    result = on_page_markdown(md, None, None, None)
    assert "oid=-102814524&id=456240009" in result
    assert "list=" not in result


def test_youtube_shorts_link():
    md = "**Антипример 1:** https://www.youtube.com/shorts/kLTpStNQRF0"
    result = on_page_markdown(md, None, None, None)
    assert (
        '<iframe class="embedded-video" '
        'src="https://www.youtube.com/embed/kLTpStNQRF0" '
        'loading="lazy" allowfullscreen></iframe>'
    ) in result


def test_unrelated_text_untouched():
    md = "Обычный текст без ссылок на видео."
    assert on_page_markdown(md, None, None, None) == md

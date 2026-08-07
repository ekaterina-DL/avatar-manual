from embed_local_media import on_page_markdown


class FakePage:
    class file:
        src_uri = "manual-3-etap/07-example-library.md"


def test_bracketed_link_still_works():
    md = "- [antiexample-1.mp4](assets/antiexample-1.mp4) — низкое качество."
    result = on_page_markdown(md, FakePage(), None, None)
    assert '<source src="assets/antiexample-1.mp4" type="video/mp4">' in result
    assert "antiexample-1.mp4</video>" in result


def test_bare_url_becomes_video():
    md = (
        "- https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/vk/"
        "26_02_2026/-76745347_456243038/-76745347_456243038.mp4 — нет синхронизации, "
        "пение выглядит неестественно."
    )
    result = on_page_markdown(md, FakePage(), None, None)
    assert (
        '<source src="https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/'
        'ak/vk/26_02_2026/-76745347_456243038/-76745347_456243038.mp4" type="video/mp4">'
        in result
    )
    assert "— нет синхронизации, пение выглядит неестественно." in result


def test_bare_url_inside_markdown_link_not_double_processed():
    md = "[кадр примера](assets/antiexample-8.jpg)"
    result = on_page_markdown(md, FakePage(), None, None)
    assert result == md  # .jpg не трогаем, это не видео

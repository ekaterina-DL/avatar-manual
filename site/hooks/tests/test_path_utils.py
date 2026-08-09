from _path_utils import fix_local_asset_path


def test_local_asset_gets_up_one_level():
    assert fix_local_asset_path("assets/timeline-correct-spacing.png") == "../assets/timeline-correct-spacing.png"
    assert fix_local_asset_path("assets/antiexample-1.mp4") == "../assets/antiexample-1.mp4"


def test_external_http_url_untouched():
    url = "https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/vk/a.mp4"
    assert fix_local_asset_path(url) == url


def test_external_http_plain_untouched():
    url = "http://example.com/assets/foo.mp4"
    assert fix_local_asset_path(url) == url


def test_already_relative_up_one_level_untouched():
    assert fix_local_asset_path("../assets/foo.png") == "../assets/foo.png"


def test_absolute_path_untouched():
    assert fix_local_asset_path("/assets/foo.png") == "/assets/foo.png"


def test_non_assets_relative_path_untouched():
    # На сегодня в мануале такого нет, но на всякий случай: трогаем только "assets/..." —
    # единственный реально встречающийся паттерн локальных ассетов (см. комментарий в
    # _path_utils.py). Другие относительные пути не переписываем, чтобы не гадать.
    assert fix_local_asset_path("other/foo.png") == "other/foo.png"

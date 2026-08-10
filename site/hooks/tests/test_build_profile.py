from _build_profile import is_pdf_build


class FakeSiteDir:
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return self._value


class FakeConfig(dict):
    def __init__(self, site_dir):
        super().__init__()
        self.site_dir = FakeSiteDir(site_dir)


def test_pdf_site_dir_is_pdf_build():
    config = FakeConfig("/repo/avatar-manual-build/build-pdf")
    assert is_pdf_build(config) is True


def test_site_site_dir_is_not_pdf_build():
    config = FakeConfig("/repo/avatar-manual-build/build")
    assert is_pdf_build(config) is False


def test_windows_style_path_is_pdf_build():
    """site_dir может прийти как WindowsPath — str() даёт обратные слэши, нормализуем их перед
    сравнением (см. Fix 3 итогового обзора)."""
    config = FakeConfig("D:\\repo\\avatar-manual-build\\build-pdf")
    assert is_pdf_build(config) is True

from _build_profile import is_pdf_build, is_public_build


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


def test_public_site_dir_is_public_build():
    config = FakeConfig("/repo/avatar-manual-build/build-public")
    assert is_public_build(config) is True


def test_windows_style_path_is_public_build():
    config = FakeConfig("D:\\repo\\avatar-manual-build\\build-public")
    assert is_public_build(config) is True


def test_profiles_do_not_overlap():
    """Суффиксы build / build-pdf / build-public различают три профиля и не пересекаются."""
    site = FakeConfig("/repo/avatar-manual-build/build")
    pdf = FakeConfig("/repo/avatar-manual-build/build-pdf")
    public = FakeConfig("/repo/avatar-manual-build/build-public")
    assert (is_pdf_build(site), is_public_build(site)) == (False, False)
    assert (is_pdf_build(pdf), is_public_build(pdf)) == (True, False)
    assert (is_pdf_build(public), is_public_build(public)) == (False, True)

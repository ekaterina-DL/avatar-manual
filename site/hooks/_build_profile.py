def is_pdf_build(config):
    """True, если текущая сборка — PDF-профиль (site/mkdocs-pdf.yml), а не обычный сайт
    (site/mkdocs.yml). mkdocs-pdf.yml задаёт site_dir=.../build-pdf, mkdocs.yml — .../build —
    это единственный надёжный сигнал отличить профиль сборки внутри хука (см. Fix 3 итогового
    обзора: раньше эта проверка была приватной копией внутри hide_site_only_sections.py —
    вынесена сюда, чтобы её могли использовать и embed_video_links.py, и
    build_segment_examples.py)."""
    return str(config.site_dir).replace("\\", "/").endswith("build-pdf")


def is_public_build(config):
    """True, если текущая сборка — публичный профиль (site/mkdocs-public.yml), который
    выкладывается на GitHub Pages. Он задаёт site_dir=.../build-public и НЕ публикует мануал
    3 этапа (он ещё в работе); обычный site/mkdocs.yml (.../build) и PDF (.../build-pdf)
    показывают весь сайт целиком. Сигнал профиля — суффикс папки сборки, как и у is_pdf_build;
    суффиксы build / build-pdf / build-public взаимно не пересекаются. См.
    hooks/public_drop_stage3.py и .github/workflows/deploy.yml."""
    return str(config.site_dir).replace("\\", "/").endswith("build-public")

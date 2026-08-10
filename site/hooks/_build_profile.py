def is_pdf_build(config):
    """True, если текущая сборка — PDF-профиль (site/mkdocs-pdf.yml), а не обычный сайт
    (site/mkdocs.yml). mkdocs-pdf.yml задаёт site_dir=.../build-pdf, mkdocs.yml — .../build —
    это единственный надёжный сигнал отличить профиль сборки внутри хука (см. Fix 3 итогового
    обзора: раньше эта проверка была приватной копией внутри hide_site_only_sections.py —
    вынесена сюда, чтобы её могли использовать и embed_video_links.py, и
    build_segment_examples.py)."""
    return str(config.site_dir).replace("\\", "/").endswith("build-pdf")

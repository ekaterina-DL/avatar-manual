from _build_profile import is_pdf_build
from _section_utils import strip_section

# Точный список (файл, заголовок) — без нечёткого сопоставления. Разделы существуют в исходных
# файлах мануала как есть, здесь только решение, что не показывать на сайте.
SECTIONS_TO_HIDE = {
    "manual-2-etap/00-overview.md": [
        "История проекта: этапы во времени",
        "Как читать этот мануал",
    ],
    "manual-3-etap/00-overview.md": [
        "История проекта во времени",
        "Как читать этот мануал",
    ],
}


def on_page_markdown(markdown, page, config, files):
    """Убирает служебные разделы (не относящиеся к содержанию инструкции) с сайта. PDF-профиль
    задуман как полный самостоятельный документ с видимыми источниками — там разделы остаются."""
    if is_pdf_build(config):
        return markdown
    src_uri = page.file.src_uri.replace("\\", "/")
    headings = SECTIONS_TO_HIDE.get(src_uri)
    if not headings:
        return markdown
    for heading in headings:
        markdown = strip_section(markdown, heading)
    return markdown

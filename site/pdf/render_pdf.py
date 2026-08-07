# site/pdf/render_pdf.py
"""Рендерит собранную print-страницу мануала (../avatar-manual-build/build-pdf/print_page/index.html)
в один PDF-файл через headless Chromium (Playwright). Отдельный шаг от `mkdocs build`,
т.к. сама генерация PDF из HTML — не задача MkDocs, а задача браузерного движка.
"""
import pathlib
from playwright.sync_api import sync_playwright

# __file__ = site/pdf/render_pdf.py; parents[0]=site/pdf, [1]=site, [2]=корень проекта,
# [3]=родитель корня проекта — см. "Исправление архитектуры" в начале плана:
# build-папка обязана лежать вне docs_dir (=корень проекта).
BUILD_DIR = pathlib.Path(__file__).resolve().parents[3] / "avatar-manual-build" / "build-pdf"
SOURCE_HTML = BUILD_DIR / "print_page" / "index.html"
OUTPUT_PDF = BUILD_DIR / "Аватар-мануал.pdf"


def main():
    if not SOURCE_HTML.exists():
        raise SystemExit(
            f"Не найден {SOURCE_HTML}. Сначала выполните: "
            f"python3 -m mkdocs build -f site/mkdocs-pdf.yml"
        )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(SOURCE_HTML.as_uri())
        # НЕ "networkidle": страница содержит ~800 <video preload="metadata"> (хук Task 4
        # встраивает все .mp4-ссылки мануала как плееры) — Chromium бесконечно догружает их
        # метаданные, networkidle не наступает и за 180 секунд (проверено при выполнении
        # Task 7). "load" + короткая пауза достаточно для CSS/веб-шрифтов; здесь важно
        # именно не блокировать сеть целиком (например, через set_offline), иначе вместе
        # с видео перестанут грузиться и веб-шрифты Google Fonts из site/theme/extra.css —
        # в PDF нужен тот же типографический вид, что и на сайте (Task 5).
        page.wait_for_load_state("load")
        page.wait_for_timeout(3000)
        page.pdf(
            path=str(OUTPUT_PDF),
            format="A4",
            print_background=True,
            margin={"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"},
        )
        browser.close()

    print(f"Готово: {OUTPUT_PDF} ({OUTPUT_PDF.stat().st_size // 1024} КБ)")


if __name__ == "__main__":
    main()

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
        # Print-страница встраивает ~800 внешних .mp4-плееров (авто-embed из Task 6).
        # В PDF видео всё равно не проигрываются, а сотни сетевых догрузок метаданных
        # не дают наступить networkidle (проверено эмпирически: без этой строки не
        # укладывается и в 180с). offline=True блокирует сетевые запросы, но не file://,
        # поэтому сама печатная страница (локальный файл) грузится и рендерится как обычно.
        page.context.set_offline(True)
        page.goto(SOURCE_HTML.as_uri())
        page.wait_for_load_state("networkidle")
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

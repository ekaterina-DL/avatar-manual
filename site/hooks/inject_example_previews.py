from pathlib import Path

from pymdownx.slugs import slugify as _pymdownx_slugify

from _section_utils import extract_section
from _list_utils import split_list_items

# Та же функция, что site/mkdocs.yml подключает для markdown_extensions.toc.slugify — иначе
# id, который реально проставит MkDocs на заголовок (например "темп-речи"), и якорь, который эта
# функция подставит в ссылку "→ ещё N прим.", могут разойтись, и клик по ссылке не долистает до
# нужного раздела (см. комментарий в mkdocs.yml — до этой правки заголовки из чистой кириллицы
# вообще получали нечитаемый id "_N", теперь оба места используют один и тот же алгоритм).
_slugify_heading = _pymdownx_slugify(case="lower")

DOCS_DIR = Path(__file__).resolve().parents[2]

# Явная таблица соответствий: где на целевой странице вставить превью, и откуда его взять.
# position="after_line" — сразу после строки, содержащей anchor; "before_line" — прямо перед ней.
MAPPINGS = [
    {
        # Каждое поле классификатора теперь своя ### -секция (12.08.2026, правка "выделить
        # каждый раздел визуально") — якоримся на заголовок СЛЕДУЮЩЕГО поля, а не на текст
        # содержимого самого поля "Темп речи": так вставка не зависит от того, как именно
        # переносится строка со значениями/цитатой внутри поля.
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "### Язык и акценты",
        "position": "before_line",
        "source_file": "manual-2-etap/11-example-library.md",
        "source_heading": "Темп речи",
        "max_items": 3,
        "label": "Темп речи",
    },
    {
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "**Смена эмоций внутри одного ролика**",
        "position": "before_line",
        "source_file": "manual-2-etap/11-example-library.md",
        "source_heading": "Эмоции",
        "max_items": 3,
        "label": "Эмоции",
    },
    {
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "### Тип речи",
        "position": "before_line",
        "source_file": "manual-2-etap/11-example-library.md",
        "source_heading": "Тип речи: диалог, монолог и закадровый голос",
        "max_items": 2,
        "label": "Тип речи",
    },
    {
        "target_file": "manual-3-etap/04-video-quality.md",
        "anchor": '## Когда сразу «Битое» (не отвечая на вопросы классификатора)',
        "position": "after_line",
        "source_file": "manual-3-etap/07-example-library.md",
        "source_heading": "1. Размечено битое видео (хотя должно было быть отправлено в «битое»)",
        "max_items": 3,
        "label": "Битое",
    },
    {
        "target_file": "manual-3-etap/04-video-quality.md",
        "anchor": '## Когда отмечать «Артефакт», но всё равно отвечать на вопросы',
        "position": "after_line",
        "source_file": "manual-3-etap/07-example-library.md",
        "source_heading": "2. Наличие артефакта (не проставлен)",
        "max_items": 3,
        "label": "Артефакт",
    },
]


def _build_preview_markdown(mapping):
    source_path = DOCS_DIR / mapping["source_file"]
    source_text = source_path.read_text(encoding="utf-8")
    section_body = extract_section(source_text, mapping["source_heading"])
    if section_body is None:
        return None
    items = split_list_items(section_body)
    if not items:
        return None
    preview_items = items[: mapping["max_items"]]
    remaining = len(items) - len(preview_items)
    # Приватный маркер для group_media_lists.py (следующий хук в пайплайне): превью вставляется
    # посреди прозы целевой страницы, без собственного markdown-заголовка — без этой строки
    # group_media_lists.py взял бы эйброу .video-block из ближайшего ПРЕДЫДУЩЕГО настоящего
    # заголовка целевой страницы (например, "Уточнения по конкретным полям..."), а не из
    # названия поля, которому реально посвящено превью. group_media_lists.py распознаёт эту
    # строку, использует её как current_heading именно с этой точки документа и вырезает саму
    # строку из финального вывода — она не должна попасть в HTML как видимый текст.
    lines = [
        "",
        f'<!-- video-eyebrow: {mapping["label"]} -->',
        '<div markdown="1">',
    ]
    if not mapping.get("skip_label"):
        lines.append("**Примеры из банка:**")
    lines.append("")
    lines.extend(preview_items)
    if remaining > 0:
        anchor = _slugify_heading(mapping["source_heading"], "-")
        link = f"{Path(mapping['source_file']).name}#{anchor}"
        lines.append(f"\n→ ещё {remaining} прим. в [банке примеров]({link})")
    # Пустая строка обязательна перед закрывающим </div> независимо от remaining: без неё, когда
    # remaining == 0 (превью показывает вообще все примеры раздела, "ещё N" не добавляется),
    # </div> оказывается на строке сразу после последнего пункта списка без пустой строки-разделителя
    # между ними. group_media_lists.py (следующий по порядку хук) сканирует список видео-пунктов и
    # останавливается только на пустой строке — без неё "</div>" ошибочно затягивается внутрь
    # последнего пункта как продолжение подписи, а _parse_video_item() затем кладёт этот "</div>"
    # прямо в caption, что даёт битую вложенность тегов на странице:
    # `<div class="vi-cap"><span markdown="1"></div></span></div>`. Обнаружено на
    # 04-classifier.md → превью "Ракурс" (ровно 2 примера в разделе-источнике = remaining 0).
    lines.append("")
    lines.append("</div>")
    lines.append("")
    return "\n".join(lines)


def _apply_mapping(markdown, mapping):
    preview = _build_preview_markdown(mapping)
    if preview is None:
        return markdown
    lines = markdown.split("\n")
    for idx, line in enumerate(lines):
        if mapping["anchor"] in line:
            insert_at = idx + 1 if mapping["position"] == "after_line" else idx
            new_lines = lines[:insert_at] + preview.split("\n") + lines[insert_at:]
            return "\n".join(new_lines)
    return markdown


def on_page_markdown(markdown, page, config, files):
    """Вставляет компактное превью (2-3 примера) из банка примеров рядом с конкретным полем
    классификатора/критерием — только там, где явно прописано соответствие в MAPPINGS. Ничего
    не выдумывает: если якорь или раздел-источник не найден, страница остаётся без изменений."""
    src_uri = page.file.src_uri.replace("\\", "/")
    applicable = [m for m in MAPPINGS if m["target_file"] == src_uri]
    if not applicable:
        return markdown
    for mapping in applicable:
        markdown = _apply_mapping(markdown, mapping)
    return markdown

# Переупаковка сайта-мануала «Аватар» — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Сделать подачу контента на сайте-мануале компактнее и понятнее: убрать служебные
разделы, встраивать видео плеером вместо ссылок, упаковать уже существующие примеры в карточки,
добавить точечные превью банка примеров у полей классификатора — без единой правки файлов
`manual-2-etap/*.md` / `manual-3-etap/*.md`.

**Architecture:** Все изменения — новые/изменённые build-хуки MkDocs (`site/hooks/*.py`,
чистые функции `markdown -> markdown`, без побочных эффектов на файловую систему мануала) плюс
CSS в `site/theme/extra.css`/`site/pdf/pdf-extra.css`. Хуки читают markdown страницы (и, для
превью примеров, ещё и сырой markdown ДРУГИХ файлов с диска только на чтение) и возвращают
изменённый markdown/HTML-фрагменты, которые дальше обрабатывает обычный конвейер MkDocs.

**Tech Stack:** Python 3 (хуки MkDocs, стандартная библиотека `re`/`pathlib`, без новых
runtime-зависимостей), pytest (только для тестов хуков, dev-зависимость), MkDocs Material
(уже используется), CSS.

## Global Constraints

- Файлы `manual-2-etap/*.md` и `manual-3-etap/*.md` не редактируются ни в одной задаче — ни на
  байт. Проверка перед коммитом каждой задачи: `git status --short manual-2-etap manual-3-etap`
  должен быть пустым.
- Каждый новый хук — чистая функция `on_page_markdown(markdown, page, config, files)`,
  без сети, без записи файлов.
- Полнота примеров сохраняется: ни один хук не имеет права молча отбросить пример, если он не
  распознал паттерн — в этом случае хук должен оставить текст как есть (без изменений), а не
  вырезать.
- Все новые CSS-переменные и классы — точные значения из
  `site/prototype-reference/template.html` (утверждённый макет), адаптированные под уже
  существующие имена переменных в `site/theme/extra.css` (см. Задача 4).
- Дизайн-документ, к которому апеллирует этот план:
  `docs/superpowers/specs/2026-08-07-site-content-restructure-design.md`.

---

## Task 1: Встраивать «голые» ссылки на .mp4 (не только `[текст](ссылка)`)

Сейчас `site/hooks/embed_local_media.py` превращает в плеер только markdown-ссылки вида
`[текст](url.mp4)`. Но в `manual-3-etap/07-example-library.md` (и потенциально в других местах)
встречаются голые ссылки вида `- https://.../....mp4 — комментарий` — без квадратных скобок.
Без этой правки они останутся кликабельными ссылками на сайте, что противоречит цели «видео
сразу плеером».

**Files:**
- Modify: `site/hooks/embed_local_media.py`
- Test: `site/hooks/tests/test_embed_local_media.py` (новый файл)
- Create: `site/hooks/tests/conftest.py` (общий для всех тестов хуков — добавляет `site/hooks`
  в `sys.path`)
- Create: `site/requirements-dev.txt`

**Interfaces:**
- Produces: `embed_local_media.on_page_markdown(markdown, page, config, files) -> str` (сигнатура
  не меняется, только результат для голых ссылок).

- [ ] **Step 1: Создать `site/requirements-dev.txt`**

```
pytest>=8.0
```

- [ ] **Step 2: Создать `site/hooks/tests/conftest.py`**

```python
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))
```

- [ ] **Step 3: Написать падающий тест на голую ссылку**

Создать `site/hooks/tests/test_embed_local_media.py`:

```python
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
```

- [ ] **Step 4: Прогнать тест, убедиться что падает**

Run: `cd site && python -m pytest hooks/tests/test_embed_local_media.py -v`
Expected: `test_bare_url_becomes_video` FAILS (bare URL остаётся ссылкой, `<source` нет в
результате).

- [ ] **Step 5: Реализовать поддержку голых ссылок**

Открыть `site/hooks/embed_local_media.py`, заменить содержимое на:

```python
import re

# [текст](путь-или-url.mp4) — ровно markdown-ссылка, ведущая на файл с расширением .mp4
BRACKETED_MP4_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+\.mp4)\)")

# Голая ссылка на .mp4, без markdown-скобок — например, в 07-example-library.md (3 этап).
# Отрицательный lookbehind на " и ( — чтобы не задеть src="..." внутри уже вставленного
# <source> (эта регулярка выполняется вторым проходом, после BRACKETED_MP4_RE) и ссылки,
# которые всё-таки были в скобках, но синтаксис которых не подошёл под первую регулярку.
BARE_MP4_RE = re.compile(r'(?<!["(])(https?://\S+?\.mp4)(?!\S)')

# Длинные обучающие видео (скачаны локально под этим префиксом) — по дизайну должны
# оставаться кликабельными ссылками, а не превращаться в плеер. См. site/PLAN.md:
# "4 длинных обучающих видео остаются кликабельными ссылками, не встраиваются плеером".
LONG_TRAINING_VIDEO_PREFIX = "training-"


def _video_tag(src, alt_text=""):
    filename = src.rsplit("/", 1)[-1]
    if filename.startswith(LONG_TRAINING_VIDEO_PREFIX):
        return None
    return (
        f'<video controls preload="metadata" style="max-width:100%">'
        f'<source src="{src}" type="video/mp4">'
        f'{alt_text}</video>'
    )


def on_page_markdown(markdown, page, config, files):
    """Превращает ссылки на .mp4 (локальные assets/ или внешние sbercloud), как markdown-ссылки
    [текст](url), так и голые url в тексте, во встроенный HTML5-плеер. Не трогает: (1) ссылки,
    не оканчивающиеся на .mp4 (например, все disk.yandex.ru/i/... — это share-страницы, а не
    прямые файлы); (2) локальные файлы с именем на training- (длинные обучающие видео) — они
    остаются обычными кликабельными ссылками, как и задумано в дизайне.
    """

    def replace_bracketed(match):
        alt_text, src = match.group(1), match.group(2)
        tag = _video_tag(src, alt_text)
        return tag if tag is not None else match.group(0)

    markdown = BRACKETED_MP4_RE.sub(replace_bracketed, markdown)

    def replace_bare(match):
        src = match.group(1)
        tag = _video_tag(src)
        return tag if tag is not None else match.group(0)

    return BARE_MP4_RE.sub(replace_bare, markdown)
```

- [ ] **Step 6: Прогнать тесты, убедиться что проходят**

Run: `cd site && python -m pytest hooks/tests/test_embed_local_media.py -v`
Expected: 3 passed.

- [ ] **Step 7: Проверить, что файлы мануала не тронуты, и закоммитить**

```bash
git status --short manual-2-etap manual-3-etap
```
Expected: пусто.

```bash
git add site/hooks/embed_local_media.py site/hooks/tests/ site/requirements-dev.txt
git commit -m "Встраивать голые ссылки на .mp4 плеером, не только markdown-ссылки [текст](url)"
```

---

## Task 2: Хук удаления служебных разделов с сайта (не из PDF)

**Files:**
- Create: `site/hooks/_section_utils.py`
- Create: `site/hooks/hide_site_only_sections.py`
- Test: `site/hooks/tests/test_section_utils.py`
- Test: `site/hooks/tests/test_hide_site_only_sections.py`

**Interfaces:**
- Produces: `_section_utils.extract_section(text: str, heading: str) -> str | None` — тело
  раздела (без заголовка), или `None` если заголовок не найден. Раздел заканчивается перед
  следующим заголовком того же или более высокого уровня, либо в конце текста.
- Produces: `_section_utils.strip_section(text: str, heading: str) -> str` — тот же текст, но с
  вырезанным разделом (включая заголовок). Если заголовок не найден — текст не меняется.
- Produces: `hide_site_only_sections.on_page_markdown(markdown, page, config, files) -> str`.
- Consumes (Task 8 будет использовать): `_section_utils.extract_section`.

- [ ] **Step 1: Написать падающий тест для `_section_utils`**

Создать `site/hooks/tests/test_section_utils.py`:

```python
from _section_utils import extract_section, strip_section

SAMPLE = """# Заголовок файла

## Раздел A

Текст A, строка 1.
Текст A, строка 2.

## Раздел Б

Текст Б.

### Подраздел Б.1

Текст подраздела.

## Раздел В

Текст В.
"""


def test_extract_middle_section_stops_before_next_heading_same_level():
    body = extract_section(SAMPLE, "Раздел A")
    assert "Текст A, строка 1." in body
    assert "Раздел Б" not in body


def test_extract_section_includes_deeper_subheadings():
    body = extract_section(SAMPLE, "Раздел Б")
    assert "Подраздел Б.1" in body
    assert "Текст подраздела." in body
    assert "Раздел В" not in body


def test_extract_last_section_goes_to_end_of_file():
    body = extract_section(SAMPLE, "Раздел В")
    assert "Текст В." in body


def test_extract_missing_heading_returns_none():
    assert extract_section(SAMPLE, "Нет такого раздела") is None


def test_strip_section_removes_heading_and_body():
    result = strip_section(SAMPLE, "Раздел Б")
    assert "Раздел Б" not in result
    assert "Подраздел Б.1" not in result
    assert "Раздел A" in result
    assert "Раздел В" in result


def test_strip_missing_heading_is_noop():
    assert strip_section(SAMPLE, "Нет такого раздела") == SAMPLE
```

- [ ] **Step 2: Прогнать тест, убедиться что падает (модуля ещё нет)**

Run: `cd site && python -m pytest hooks/tests/test_section_utils.py -v`
Expected: FAIL с `ModuleNotFoundError: No module named '_section_utils'`.

- [ ] **Step 3: Реализовать `_section_utils.py`**

Создать `site/hooks/_section_utils.py`:

```python
import re

_HEADING_RE = re.compile(r'^(#{1,6})\s+(.*?)\s*$')


def _find_heading(lines, heading):
    for i, line in enumerate(lines):
        match = _HEADING_RE.match(line)
        if match and match.group(2) == heading:
            return i, len(match.group(1))
    return None, None


def extract_section(text, heading):
    """Тело раздела с заданным заголовком (без строки заголовка), до следующего заголовка
    того же или более высокого уровня, либо до конца текста. None, если заголовок не найден."""
    lines = text.split("\n")
    start, level = _find_heading(lines, heading)
    if start is None:
        return None
    body_lines = []
    for line in lines[start + 1:]:
        match = _HEADING_RE.match(line)
        if match and len(match.group(1)) <= level:
            break
        body_lines.append(line)
    return "\n".join(body_lines)


def strip_section(text, heading):
    """Текст без раздела heading (включая строку заголовка). Без изменений, если не найден."""
    lines = text.split("\n")
    start, level = _find_heading(lines, heading)
    if start is None:
        return text
    end = start + 1
    for line in lines[start + 1:]:
        match = _HEADING_RE.match(line)
        if match and len(match.group(1)) <= level:
            break
        end += 1
    return "\n".join(lines[:start] + lines[end:])
```

- [ ] **Step 4: Прогнать тест, убедиться что проходит**

Run: `cd site && python -m pytest hooks/tests/test_section_utils.py -v`
Expected: 6 passed.

- [ ] **Step 5: Написать падающий тест для `hide_site_only_sections`**

Создать `site/hooks/tests/test_hide_site_only_sections.py`:

```python
from hide_site_only_sections import on_page_markdown

OVERVIEW_2ETAP = """# Обзор

## Порог качества по ходу работы (не путать с порогом экзамена)

Текст порога качества.

## История проекта: этапы во времени

Текст истории, не должен остаться.

## Обучение и входной экзамен «Ступень 2»

Текст обучения.

## Как читать этот мануал

Текст про то как читать.
"""


class FakeFile:
    def __init__(self, src_uri):
        self.src_uri = src_uri


class FakePage:
    def __init__(self, src_uri):
        self.file = FakeFile(src_uri)


class FakeSiteDir:
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return self._value


class FakeConfig(dict):
    def __init__(self, site_dir):
        super().__init__()
        self.site_dir = FakeSiteDir(site_dir)


def test_removes_both_sections_on_site_build():
    page = FakePage("manual-2-etap/00-overview.md")
    config = FakeConfig("/repo/avatar-manual-build/build")
    result = on_page_markdown(OVERVIEW_2ETAP, page, config, None)
    assert "История проекта" not in result
    assert "Как читать этот мануал" not in result
    assert "Текст порога качества." in result
    assert "Текст обучения." in result


def test_untouched_on_pdf_build():
    page = FakePage("manual-2-etap/00-overview.md")
    config = FakeConfig("/repo/avatar-manual-build/build-pdf")
    result = on_page_markdown(OVERVIEW_2ETAP, page, config, None)
    assert result == OVERVIEW_2ETAP


def test_untouched_on_unrelated_page():
    page = FakePage("manual-2-etap/01-general-requirements.md")
    config = FakeConfig("/repo/avatar-manual-build/build")
    result = on_page_markdown(OVERVIEW_2ETAP, page, config, None)
    assert result == OVERVIEW_2ETAP
```

- [ ] **Step 6: Прогнать тест, убедиться что падает**

Run: `cd site && python -m pytest hooks/tests/test_hide_site_only_sections.py -v`
Expected: FAIL, модуля `hide_site_only_sections` нет.

- [ ] **Step 7: Реализовать хук**

Создать `site/hooks/hide_site_only_sections.py`:

```python
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


def _is_pdf_build(config):
    # mkdocs-pdf.yml задаёт site_dir=.../build-pdf, mkdocs.yml — .../build.
    return str(config.site_dir).replace("\\", "/").endswith("build-pdf")


def on_page_markdown(markdown, page, config, files):
    """Убирает служебные разделы (не относящиеся к содержанию инструкции) с сайта. PDF-профиль
    задуман как полный самостоятельный документ с видимыми источниками — там разделы остаются."""
    if _is_pdf_build(config):
        return markdown
    src_uri = page.file.src_uri.replace("\\", "/")
    headings = SECTIONS_TO_HIDE.get(src_uri)
    if not headings:
        return markdown
    for heading in headings:
        markdown = strip_section(markdown, heading)
    return markdown
```

- [ ] **Step 8: Прогнать тесты, убедиться что проходят**

Run: `cd site && python -m pytest hooks/tests/test_hide_site_only_sections.py -v`
Expected: 3 passed.

- [ ] **Step 9: Проверить файлы мануала и закоммитить**

```bash
git status --short manual-2-etap manual-3-etap
git add site/hooks/_section_utils.py site/hooks/hide_site_only_sections.py site/hooks/tests/test_section_utils.py site/hooks/tests/test_hide_site_only_sections.py
git commit -m "Хук: убрать 'История проекта' и 'Как читать этот мануал' с сайта (не из PDF)"
```

---

## Task 3: Хук встраивания VK-видео и YouTube Shorts плеером

Технически проверено (см. дизайн-документ): `https://vk.com/video_ext.php?oid=...&id=...&hd=2`
отдаёт рабочий плеер (HTTP 200) без пароля для этих публичных видео.

**Files:**
- Create: `site/hooks/embed_video_links.py`
- Test: `site/hooks/tests/test_embed_video_links.py`
- Modify: `site/theme/extra.css` (добавить `.embedded-video`)

**Interfaces:**
- Produces: `embed_video_links.on_page_markdown(markdown, page, config, files) -> str`. Выходной
  HTML использует класс `embedded-video` на `<iframe>` — на этот класс опирается CSS
  (16:9 responsive) и будущие хуки (Задача 7 ищет `<iframe` в тексте, не привязываясь к классу).

- [ ] **Step 1: Написать падающий тест**

Создать `site/hooks/tests/test_embed_video_links.py`:

```python
from embed_video_links import on_page_markdown


def test_vk_link_with_positive_owner():
    md = "**Пример 1:** https://vkvideo.ru/video712360465_456239217"
    result = on_page_markdown(md, None, None, None)
    assert (
        '<iframe class="embedded-video" '
        'src="https://vk.com/video_ext.php?oid=712360465&id=456239217&hd=2" '
        'loading="lazy" allowfullscreen></iframe>'
    ) in result


def test_vk_link_with_negative_owner():
    md = "**Пример 2:** https://vkvideo.ru/video-45280055_456240146"
    result = on_page_markdown(md, None, None, None)
    assert "oid=-45280055&id=456240146" in result


def test_vk_link_with_query_string_is_stripped():
    md = "**Пример 4:** https://vkvideo.ru/video-102814524_456240009?list=ln-6LGJHsXLGhcRMCXpnl"
    result = on_page_markdown(md, None, None, None)
    assert "oid=-102814524&id=456240009" in result
    assert "list=" not in result


def test_youtube_shorts_link():
    md = "**Антипример 1:** https://www.youtube.com/shorts/kLTpStNQRF0"
    result = on_page_markdown(md, None, None, None)
    assert (
        '<iframe class="embedded-video" '
        'src="https://www.youtube.com/embed/kLTpStNQRF0" '
        'loading="lazy" allowfullscreen></iframe>'
    ) in result


def test_unrelated_text_untouched():
    md = "Обычный текст без ссылок на видео."
    assert on_page_markdown(md, None, None, None) == md
```

- [ ] **Step 2: Прогнать тест, убедиться что падает**

Run: `cd site && python -m pytest hooks/tests/test_embed_video_links.py -v`
Expected: FAIL, модуля нет.

- [ ] **Step 3: Реализовать хук**

Создать `site/hooks/embed_video_links.py`:

```python
import re

VK_RE = re.compile(r'https?://vkvideo\.ru/video(-?\d+)_(\d+)(?:\?\S*)?')
YOUTUBE_SHORTS_RE = re.compile(r'https?://(?:www\.)?youtube\.com/shorts/([A-Za-z0-9_-]+)')


def _embed_vk(match):
    oid, video_id = match.group(1), match.group(2)
    return (
        f'<iframe class="embedded-video" '
        f'src="https://vk.com/video_ext.php?oid={oid}&id={video_id}&hd=2" '
        f'loading="lazy" allowfullscreen></iframe>'
    )


def _embed_youtube(match):
    video_id = match.group(1)
    return (
        f'<iframe class="embedded-video" '
        f'src="https://www.youtube.com/embed/{video_id}" '
        f'loading="lazy" allowfullscreen></iframe>'
    )


def on_page_markdown(markdown, page, config, files):
    """Превращает голые ссылки на vkvideo.ru и youtube.com/shorts во встроенный iframe-плеер.
    loading="lazy" — нативная отложенная загрузка браузера, без JS."""
    markdown = VK_RE.sub(_embed_vk, markdown)
    markdown = YOUTUBE_SHORTS_RE.sub(_embed_youtube, markdown)
    return markdown
```

- [ ] **Step 4: Прогнать тест, убедиться что проходит**

Run: `cd site && python -m pytest hooks/tests/test_embed_video_links.py -v`
Expected: 5 passed.

- [ ] **Step 5: Добавить CSS для `.embedded-video`**

В `site/theme/extra.css` добавить в конец файла:

```css
/* Встроенный плеер VK/YouTube (хук embed_video_links.py, Task 3 плана переупаковки) */
.embedded-video {
  width: 100%;
  aspect-ratio: 16 / 9;
  border: 0;
  display: block;
  border-radius: 4px;
  margin: 1em 0;
}
```

- [ ] **Step 6: Проверить файлы мануала и закоммитить**

```bash
git status --short manual-2-etap manual-3-etap
git add site/hooks/embed_video_links.py site/hooks/tests/test_embed_video_links.py site/theme/extra.css
git commit -m "Хук: встраивать vkvideo.ru и youtube.com/shorts плеером вместо голой ссылки"
```

---

## Task 4: Картинки маленькими карточками с zoom по наведению (кроме списка исключений)

Чистый CSS, без хуков. Правило источника: генерическое правило — **раньше** в файле (ниже
специфичности), специфика карточек из задач 6-7 добавляется **позже** в файле — так при равной
специфичности побеждают более поздние правила по каскаду.

**Files:**
- Modify: `site/theme/extra.css`

**Interfaces:**
- Не применимо (только CSS).

- [ ] **Step 1: Добавить переменные макета, недостающие в текущей палитре**

В `site/theme/extra.css`, внутри существующего блока `:root { ... }` (после текущих переменных,
перед закрывающей `}`), добавить:

```css
  /* Доп. переменные для карточек (Task 4-7 плана переупаковки) — точные значения
     с утверждённого макета, см. site/prototype-reference/README.md */
  --card-line: rgba(27, 34, 38, 0.13);
  --card-shadow: 0 1px 2px rgba(20, 24, 27, .04), 0 8px 24px -12px rgba(20, 24, 27, .18);
  --card-shadow-hover: 0 22px 46px -12px rgba(0, 0, 0, .45), 0 0 0 1px rgba(27, 34, 38, .22);
  --accent-bg: rgba(185, 106, 34, 0.10);
  --accent-ink: #8F5119;
```

- [ ] **Step 2: Добавить генерическое правило картинок-миниатюр**

В конец `site/theme/extra.css` добавить (это должно идти ДО блоков из задач 6/7 — так что
следующие задачи дописывают файл ниже этого блока):

```css
/* Картинки в тексте — маленькие карточки, увеличиваются по наведению курсора.
   Исключение — интерфейсные/справочные изображения, см. список ниже. */
.md-typeset img {
  max-width: 220px;
  max-height: 220px;
  width: auto;
  border-radius: 10px;
  border: 1px solid var(--gray-300);
  box-shadow: var(--card-shadow);
  cursor: zoom-in;
  transition: transform .22s ease, box-shadow .22s ease;
  position: relative;
}
.md-typeset img:hover {
  transform: scale(1.8);
  z-index: 30;
  box-shadow: var(--card-shadow-hover);
}

/* Исключения: интерфейсные скриншоты и плотные справочные диаграммы — остаются
   крупными и читаемыми, без уменьшения и без zoom по наведению. */
.md-typeset img[src$="interface-overview.jpeg"],
.md-typeset img[src$="classifier-panel-fields.png"],
.md-typeset img[src$="classifier-single-checkboxes.png"],
.md-typeset img[src$="classifier-multi-checkboxes.png"],
.md-typeset img[src$="trim-buttons.png"],
.md-typeset img[src$="anthropomorph-calibration-chart.png"] {
  max-width: 100%;
  max-height: none;
  border-radius: 4px;
  box-shadow: none;
  cursor: default;
  transition: none;
}
.md-typeset img[src$="interface-overview.jpeg"]:hover,
.md-typeset img[src$="classifier-panel-fields.png"]:hover,
.md-typeset img[src$="classifier-single-checkboxes.png"]:hover,
.md-typeset img[src$="classifier-multi-checkboxes.png"]:hover,
.md-typeset img[src$="trim-buttons.png"]:hover,
.md-typeset img[src$="anthropomorph-calibration-chart.png"]:hover {
  transform: none;
  z-index: auto;
  box-shadow: none;
}
```

- [ ] **Step 3: Локальная визуальная проверка**

```bash
cd site && mkdocs serve -f mkdocs.yml
```

Открыть в браузере `http://127.0.0.1:8000/manual-2-etap/05-what-to-label/` — проверить, что
картинка `cars-not-anthropomorphic.png` маленькая и увеличивается по наведению. Открыть
`http://127.0.0.1:8000/manual-2-etap/02-segments/` (раздел «Интерфейс разметки») — проверить,
что `interface-overview.jpeg` осталась крупной. Остановить сервер (Ctrl+C).

- [ ] **Step 4: Проверить файлы мануала и закоммитить**

```bash
git status --short manual-2-etap manual-3-etap
git add site/theme/extra.css
git commit -m "CSS: картинки — маленькие карточки с zoom по наведению, кроме интерфейсных скриншотов"
```

---

## Task 5: Хук группировки списков видео в компактную сетку `.video-block`

Там, где в тексте уже сейчас подряд идут пункты списка, каждый из которых — один пример-видео
(из Task 1/3, уже встроенный как `<video>`), упаковываем группу в `.video-block`/`.video-grid`.
Одиночные видео (не в списке или единственный пункт) не трогаем.

**Files:**
- Create: `site/hooks/_list_utils.py`
- Create: `site/hooks/group_media_lists.py`
- Test: `site/hooks/tests/test_list_utils.py`
- Test: `site/hooks/tests/test_group_media_lists.py`
- Modify: `site/theme/extra.css` (добавить `.video-block` и связанные классы)

**Interfaces:**
- Produces: `_list_utils.split_list_items(text: str) -> list[str]` — список пунктов
  верхнеуровневого маркированного списка (`- `), каждый пункт включает свои обёрнутые
  (продолженные без пустой строки) строки как один элемент.
- Produces: `group_media_lists.on_page_markdown(markdown, page, config, files) -> str`.

- [ ] **Step 1: Написать падающий тест для `_list_utils`**

Создать `site/hooks/tests/test_list_utils.py`:

```python
from _list_utils import split_list_items

def test_single_line_items():
    text = "- один\n- два\n- три"
    assert split_list_items(text) == ["- один", "- два", "- три"]


def test_wrapped_continuation_line_stays_in_same_item():
    text = (
        "- первый пункт с продолжением,\n"
        "  которое идёт на второй строке.\n"
        "- второй пункт."
    )
    items = split_list_items(text)
    assert len(items) == 2
    assert "которое идёт на второй строке." in items[0]
    assert items[1] == "- второй пункт."


def test_blank_line_ends_the_list():
    text = "- пункт один\n\nобычный текст после списка"
    items = split_list_items(text)
    assert items == ["- пункт один"]
```

- [ ] **Step 2: Прогнать, убедиться что падает**

Run: `cd site && python -m pytest hooks/tests/test_list_utils.py -v`
Expected: FAIL, модуля нет.

- [ ] **Step 3: Реализовать `_list_utils.py`**

Создать `site/hooks/_list_utils.py`:

```python
import re

_ITEM_START_RE = re.compile(r'^-\s+')


def split_list_items(text):
    """Разбивает текст маркированного списка на пункты верхнего уровня. Строки-продолжения
    (без "- " в начале, идущие сразу за пунктом без пустой строки) остаются частью того же
    пункта. Пустая строка или конец текста — граница списка."""
    items = []
    current = []
    for line in text.split("\n"):
        if _ITEM_START_RE.match(line):
            if current:
                items.append("\n".join(current))
            current = [line]
        elif current and line.strip():
            current.append(line)
        else:
            if current:
                items.append("\n".join(current))
                current = []
    if current:
        items.append("\n".join(current))
    return items
```

- [ ] **Step 4: Прогнать, убедиться что проходит**

Run: `cd site && python -m pytest hooks/tests/test_list_utils.py -v`
Expected: 3 passed.

- [ ] **Step 5: Написать падающий тест для `group_media_lists`**

Создать `site/hooks/tests/test_group_media_lists.py`:

```python
from group_media_lists import on_page_markdown


def test_groups_two_consecutive_video_items():
    md = (
        '## Примеры «Битое» (для калибровки, что считается явным браком)\n\n'
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/a.mp4" type="video/mp4">'
        'Низкое качество, полоса в районе рта</video>.\n'
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/b.mp4" type="video/mp4">'
        '3 склейки подряд</video>.\n'
    )
    result = on_page_markdown(md, None, None, None)
    assert '<div class="video-block">' in result
    assert result.count('<div class="video-item">') == 2
    assert 'src="https://example.com/a.mp4"' in result
    assert "Низкое качество, полоса в районе рта." in result
    assert "3 склейки подряд." in result
    assert '<span class="eyebrow">Примеры «Битое» (для калибровки, что считается явным браком)</span>' in result


def test_handles_wrapped_caption_and_trailing_text_after_video_tag():
    md = (
        '## Артефакты, которые всё ещё допустимы (примеры на грани)\n\n'
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/a.mp4" type="video/mp4">'
        'Мутные глаза, мелкая пиксельность, засвет сверху</video> — если мимика всё равно видна неплохо,\n'
        '  такой фрагмент разметить можно.\n'
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/b.mp4" type="video/mp4">'
        'Мелкая пиксельность, небольшая дымка на видео</video> — допустимо.\n'
    )
    result = on_page_markdown(md, None, None, None)
    assert '<div class="video-block">' in result
    assert "если мимика всё равно видна неплохо, такой фрагмент разметить можно." in result


def test_single_video_item_not_grouped():
    md = (
        "## Раздел\n\n"
        '- <video controls preload="metadata" style="max-width:100%">'
        '<source src="https://example.com/a.mp4" type="video/mp4">Одиночный пример</video>.\n'
    )
    result = on_page_markdown(md, None, None, None)
    assert "video-block" not in result
    assert "<video" in result


def test_non_video_list_untouched():
    md = "## Раздел\n\n- обычный пункт\n- ещё один пункт\n"
    assert on_page_markdown(md, None, None, None) == md
```

- [ ] **Step 6: Прогнать, убедиться что падает**

Run: `cd site && python -m pytest hooks/tests/test_group_media_lists.py -v`
Expected: FAIL, модуля нет.

- [ ] **Step 7: Реализовать хук**

Создать `site/hooks/group_media_lists.py`:

```python
import re

from _list_utils import split_list_items

_HEADING_RE = re.compile(r'^(#{2,6})\s+(.*?)\s*$')
_ITEM_START_RE = re.compile(r'^-\s+')
_VIDEO_ITEM_RE = re.compile(
    r'^-\s*<video\b[^>]*><source\s+src="([^"]+)"\s+type="video/mp4">(.*?)</video>(.*)$',
    re.DOTALL,
)


def _flatten(item_text):
    return re.sub(r'\n\s*', ' ', item_text).strip()


def _parse_video_item(item_text):
    match = _VIDEO_ITEM_RE.match(_flatten(item_text))
    if not match:
        return None
    src, inner_caption, trailing = match.groups()
    caption = (inner_caption + trailing).strip()
    return src, caption


def _render_video_block(heading, items):
    cards = []
    for src, caption in items:
        cap_html = (
            f'<div class="vi-cap"><span markdown="1">{caption}</span></div>'
            if caption.strip(" .")
            else ""
        )
        cards.append(
            '<div class="video-item">'
            f'<video controls preload="metadata" src="{src}"></video>'
            f'{cap_html}'
            "</div>"
        )
    eyebrow = f'<span class="eyebrow">{heading}</span>' if heading else ""
    return (
        '<div class="video-block">'
        f'<div class="vb-head">{eyebrow}</div>'
        f'<div class="video-grid">{"".join(cards)}</div>'
        "</div>"
    )


def on_page_markdown(markdown, page, config, files):
    """Находит подряд идущие пункты списка (2 и более), каждый из которых — ровно один
    встроенный <video>, и оборачивает такую группу в .video-block/.video-grid. Одиночные
    видео-пункты и любые другие списки не трогает."""
    lines = markdown.split("\n")
    out_lines = []
    current_heading = ""
    i = 0
    n = len(lines)
    while i < n:
        heading_match = _HEADING_RE.match(lines[i])
        if heading_match:
            current_heading = heading_match.group(2)
            out_lines.append(lines[i])
            i += 1
            continue

        if _ITEM_START_RE.match(lines[i]):
            j = i
            while j < n and (lines[j].strip() != "" or j == i):
                if j > i and lines[j].strip() == "":
                    break
                j += 1
            list_lines = lines[i:j]
            items = split_list_items("\n".join(list_lines))
            parsed = [_parse_video_item(item) for item in items]
            if items and all(p is not None for p in parsed) and len(items) >= 2:
                out_lines.append(_render_video_block(current_heading, parsed))
            else:
                out_lines.extend(list_lines)
            i = j
            continue

        out_lines.append(lines[i])
        i += 1
    return "\n".join(out_lines)
```

- [ ] **Step 8: Прогнать тесты, убедиться что проходят**

Run: `cd site && python -m pytest hooks/tests/test_group_media_lists.py hooks/tests/test_list_utils.py -v`
Expected: 7 passed. Если `test_handles_wrapped_caption_and_trailing_text_after_video_tag` падает
из-за форматирования пробелов вокруг «—», поправить сборку `caption` в `_parse_video_item`
(например, `caption = re.sub(r'\s+', ' ', inner_caption + trailing).strip()`), перезапустить.

- [ ] **Step 9: Добавить CSS для `.video-block`**

В `site/theme/extra.css` добавить (после блока из Task 4):

```css
/* Сетка карточек-видео, собираемая хуком group_media_lists.py (Task 5) */
.video-block {
  margin: 1.6em 0;
  border: 1px solid var(--card-line);
  border-radius: 12px;
  padding: 16px;
  background: var(--gray-50);
  box-shadow: var(--card-shadow);
}
.video-block .vb-head { margin-bottom: 12px; }
.video-block .eyebrow {
  font-family: 'Golos Text', sans-serif;
  font-size: .72rem;
  font-weight: 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--gray-600);
}
.video-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
@media (max-width: 560px) { .video-grid { grid-template-columns: 1fr; } }
.video-item {
  border-radius: 9px;
  overflow: hidden;
  border: 1px solid var(--card-line);
}
.video-item video {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  display: block;
  background: #000;
  max-height: 320px;
  margin: 0;
  border: none;
  border-radius: 0;
}
.video-item .vi-cap {
  padding: 8px 11px;
  font-family: 'Golos Text', sans-serif;
  font-size: .78rem;
  background: var(--gray-100);
}
```

- [ ] **Step 10: Проверить файлы мануала и закоммитить**

```bash
git status --short manual-2-etap manual-3-etap
git add site/hooks/_list_utils.py site/hooks/group_media_lists.py site/hooks/tests/test_list_utils.py site/hooks/tests/test_group_media_lists.py site/theme/extra.css
git commit -m "Хук: упаковывать списки видео-примеров в компактную сетку .video-block"
```

---

## Task 6: Хук карточек сравнения «Правильно/Неправильно» с картинками

**Files:**
- Create: `site/hooks/build_compare_cards.py`
- Test: `site/hooks/tests/test_build_compare_cards.py`
- Modify: `site/theme/extra.css` (добавить `.compare`/`.compare-card`)

**Interfaces:**
- Produces: `build_compare_cards.on_page_markdown(markdown, page, config, files) -> str`.

- [ ] **Step 1: Написать падающий тест**

Создать `site/hooks/tests/test_build_compare_cards.py` (таблица — точная копия
`manual-2-etap/02-segments.md:110-113`):

```python
from build_compare_cards import on_page_markdown

TABLE_MD = (
    "Между сегментами должен быть зазор.\n\n"
    "| Правильно | Неправильно |\n"
    "|---|---|\n"
    "| ![Так правильно: два сегмента на таймлайне с зазором между ними]"
    "(assets/timeline-correct-spacing.png) | ![Так неправильно: два сегмента "
    "перекрываются, есть тёмная зона наложения](assets/timeline-incorrect-overlap.png) |\n"
    "| Между красным и зелёным сегментом есть промежуток | Красный и зелёный сегмент "
    "налезают друг на друга (тёмно-зелёная зона) |\n"
)


def test_converts_table_to_compare_cards():
    result = on_page_markdown(TABLE_MD, None, None, None)
    assert '<div class="compare">' in result
    assert '<div class="compare-card good">' in result
    assert '<div class="compare-card bad">' in result
    assert 'src="assets/timeline-correct-spacing.png"' in result
    assert 'src="assets/timeline-incorrect-overlap.png"' in result
    assert "✓ Правильно" in result
    assert "✗ Неправильно" in result
    assert "Между красным и зелёным сегментом есть промежуток" in result
    assert "Красный и зелёный сегмент налезают друг на друга" in result
    assert "Между сегментами должен быть зазор." in result  # текст до таблицы сохранён


def test_table_without_images_untouched():
    md = "| Правильно | Неправильно |\n|---|---|\n| да | нет |\n"
    assert on_page_markdown(md, None, None, None) == md


def test_no_table_untouched():
    md = "Обычный текст без таблиц."
    assert on_page_markdown(md, None, None, None) == md
```

- [ ] **Step 2: Прогнать, убедиться что падает**

Run: `cd site && python -m pytest hooks/tests/test_build_compare_cards.py -v`
Expected: FAIL, модуля нет.

- [ ] **Step 3: Реализовать хук**

Создать `site/hooks/build_compare_cards.py`:

```python
import re

_TABLE_RE = re.compile(
    r'\|\s*Правильно\s*\|\s*Неправильно\s*\|\n'
    r'\|[-: ]+\|[-: ]+\|\n'
    r'\|\s*!\[([^\]]*)\]\(([^)]+)\)\s*\|\s*!\[([^\]]*)\]\(([^)]+)\)\s*\|\n'
    r'\|\s*([^|\n]*?)\s*\|\s*([^|\n]*?)\s*\|'
)


def _render(match):
    alt_good, src_good, alt_bad, src_bad, cap_good, cap_bad = match.groups()
    return (
        '<div class="compare">'
        '<div class="compare-card good">'
        f'<img src="{src_good}" alt="{alt_good}">'
        '<div class="compare-tag">✓ Правильно</div>'
        f'<div class="compare-cap"><span markdown="1">{cap_good}</span></div>'
        '</div>'
        '<div class="compare-card bad">'
        f'<img src="{src_bad}" alt="{alt_bad}">'
        '<div class="compare-tag">✗ Неправильно</div>'
        f'<div class="compare-cap"><span markdown="1">{cap_bad}</span></div>'
        '</div>'
        '</div>'
    )


def on_page_markdown(markdown, page, config, files):
    """Двухколоночная таблица с заголовками ровно "Правильно"/"Неправильно", где в первой
    строке данных — картинки, а во второй — подписи, превращается в .compare/.compare-card
    (картинка с zoom по наведению, цветная плашка, подпись). Таблицы без картинок или с другими
    заголовками не трогает."""
    return _TABLE_RE.sub(_render, markdown)
```

- [ ] **Step 4: Прогнать, убедиться что проходит**

Run: `cd site && python -m pytest hooks/tests/test_build_compare_cards.py -v`
Expected: 3 passed.

- [ ] **Step 5: Добавить CSS**

В `site/theme/extra.css` добавить (после блока Task 5):

```css
/* Карточки сравнения "Правильно/Неправильно", собираемые build_compare_cards.py (Task 6) */
.compare {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin: 1.4em 0;
}
@media (max-width: 560px) { .compare { grid-template-columns: 1fr; } }
.compare-card {
  border-radius: 10px;
  border: 1px solid var(--card-line);
  background: var(--gray-50);
  box-shadow: var(--card-shadow);
}
.compare-card.good { border-color: var(--ok-color); }
.compare-card.bad { border-color: var(--no-color); }
.compare-card img {
  max-width: 100%;
  max-height: none;
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  display: block;
  border-radius: 10px 10px 0 0;
  border: none;
  margin: 0;
  cursor: zoom-in;
  transition: transform .22s ease, box-shadow .22s ease;
}
.compare-card:hover img {
  transform: scale(1.9);
  transform-origin: top center;
  z-index: 30;
  box-shadow: var(--card-shadow-hover);
}
.compare-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-family: 'Golos Text', sans-serif;
  font-size: .76rem;
  font-weight: 700;
}
.compare-card.good .compare-tag { background: var(--ok-bg); color: var(--ok-color); }
.compare-card.bad .compare-tag { background: var(--no-bg); color: var(--no-color); }
.compare-cap {
  padding: 10px 12px 13px;
  font-size: .85rem;
  color: var(--gray-600);
  line-height: 1.55;
}
```

- [ ] **Step 6: Проверить файлы мануала и закоммитить**

```bash
git status --short manual-2-etap manual-3-etap
git add site/hooks/build_compare_cards.py site/hooks/tests/test_build_compare_cards.py site/theme/extra.css
git commit -m "Хук: таблица Правильно/Неправильно с картинками -> карточки сравнения"
```

---

## Task 7: Хук карточек примеров для `02-segments.md` (`.example-grid`)

Специфичный для одной страницы хук: превращает блоки `**Пример N:**`/`**Антипример N:**` (уже с
встроенным видео из Task 3) в сетку карточек. Должен идти в конвейере после
`embed_video_links.py`.

**Files:**
- Create: `site/hooks/build_segment_examples.py`
- Test: `site/hooks/tests/test_build_segment_examples.py`
- Modify: `site/theme/extra.css` (добавить `.example-grid`/`.example-card`)

**Interfaces:**
- Consumes: строки вида `**Пример N:** <iframe class="embedded-video" ...></iframe>` — то есть
  ожидает, что `embed_video_links.py` уже отработал на этой же странице раньше в конвейере.
- Produces: `build_segment_examples.on_page_markdown(markdown, page, config, files) -> str`.

- [ ] **Step 1: Написать падающий тест**

Создать `site/hooks/tests/test_build_segment_examples.py` (фикстура — реальная структура
`manual-2-etap/02-segments.md`, но с укороченным iframe для читаемости теста):

```python
from build_segment_examples import on_page_markdown

IFRAME_1 = '<iframe class="embedded-video" src="https://vk.com/video_ext.php?oid=1&id=1&hd=2" loading="lazy" allowfullscreen></iframe>'
IFRAME_2 = '<iframe class="embedded-video" src="https://vk.com/video_ext.php?oid=2&id=2&hd=2" loading="lazy" allowfullscreen></iframe>'
IFRAME_3 = '<iframe class="embedded-video" src="https://vk.com/video_ext.php?oid=3&id=3&hd=2" loading="lazy" allowfullscreen></iframe>'

SEGMENTS_MD = f"""## Примеры (позитивные)

**Пример 1:** {IFRAME_1}
![Пример 1: женщина на нейтральном тёмном фоне, говорит](assets/example1-frame.jpeg)
Отрывок с речью. Можно выделить сегмент от 10 сек.
**Подходящий сегмент: 0:02 – 02:57.**

**Пример 2:** {IFRAME_2}
![Пример 2: девушка поёт у пианино](assets/example2-frame.jpeg)
Отрывок с пением.
**Подходящие сегменты:**
- сегмент с плечами: 0:08 – 0:37
- сегмент с появлением рук: 0:37 – 02:40

`[Инстр. Kandinsky-Аватар, стр.5-7]`

## Антипримеры

**Антипример 1:** {IFRAME_3}
![Антипример 1: вертикальное видео](assets/antiexample1-frame.jpeg)
1. Не должно быть сопроводительных текстов на видео.
2. В видео должна быть хотя бы одна непрерывная сцена.

`[Инстр. Kandinsky-Аватар, стр.7-10]`
"""


class FakeFile:
    src_uri = "manual-2-etap/02-segments.md"


class FakePage:
    file = FakeFile()


def test_builds_two_grids_positive_and_negative():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), None, None)
    assert result.count('<div class="example-grid">') == 2
    assert result.count('<div class="example-card">') == 2  # два положительных
    assert result.count('<div class="example-card bad">') == 1  # один антипример


def test_card_contains_iframe_not_static_image():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), None, None)
    assert IFRAME_1 in result
    assert 'src="assets/example1-frame.jpeg"' not in result


def test_card_preserves_full_caption_including_nested_list():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), None, None)
    assert "сегмент с появлением рук: 0:37 – 02:40" in result
    assert "Подходящие сегменты" in result


def test_card_preserves_numbered_caption():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), None, None)
    assert "непрерывная сцена" in result


def test_source_tag_kept_outside_cards():
    result = on_page_markdown(SEGMENTS_MD, FakePage(), None, None)
    assert "[Инстр. Kandinsky-Аватар, стр.5-7]" in result
    assert "[Инстр. Kandinsky-Аватар, стр.7-10]" in result


def test_untouched_on_other_pages():
    class OtherFile:
        src_uri = "manual-2-etap/04-classifier.md"

    class OtherPage:
        file = OtherFile()

    assert on_page_markdown(SEGMENTS_MD, OtherPage(), None, None) == SEGMENTS_MD
```

- [ ] **Step 2: Прогнать, убедиться что падает**

Run: `cd site && python -m pytest hooks/tests/test_build_segment_examples.py -v`
Expected: FAIL, модуля нет.

- [ ] **Step 3: Реализовать хук**

Создать `site/hooks/build_segment_examples.py`:

```python
import re

from _section_utils import extract_section

TARGET_FILE = "manual-2-etap/02-segments.md"
SECTION_HEADINGS = ["Примеры (позитивные)", "Антипримеры"]

_BLOCK_START_RE = re.compile(
    r'\*\*((?:Анти)?[Пп]ример) (\d+):\*\*[ \t]*(<iframe.*?</iframe>)[ \t]*\n'
)
_IMAGE_LINE_RE = re.compile(r'!\[[^\]]*\]\([^)]+\)\n?')
_SOURCE_TAG_RE = re.compile(r'\n(`\[[^`\n]*\]`)\s*$')


def _split_blocks(section_body):
    starts = list(_BLOCK_START_RE.finditer(section_body))
    blocks = []
    for idx, match in enumerate(starts):
        block_end = starts[idx + 1].start() if idx + 1 < len(starts) else len(section_body)
        blocks.append((match, section_body[match.start():block_end]))
    return blocks


def _parse_block(match, block_text):
    kind, number, iframe_html = match.groups()
    rest = block_text[match.end() - match.start():]
    rest = _IMAGE_LINE_RE.sub("", rest, count=1)
    caption = rest.strip()
    is_bad = kind.startswith("Анти")
    return is_bad, number, iframe_html, caption


def _render_card(is_bad, number, iframe_html, caption):
    card_class = "example-card bad" if is_bad else "example-card"
    return (
        f'<div class="{card_class}">'
        f'{iframe_html}'
        '<div class="ec-body">'
        f'<span class="num">{number}</span>'
        f'<div markdown="1">{caption}</div>'
        "</div>"
        "</div>"
    )


def _transform_section(markdown, heading):
    body = extract_section(markdown, heading)
    if body is None:
        return markdown
    blocks = _split_blocks(body)
    if not blocks:
        return markdown

    trailing = []
    cards = []
    for match, block_text in blocks:
        is_bad, number, iframe_html, caption = _parse_block(match, block_text)
        tag_match = _SOURCE_TAG_RE.search(caption)
        if tag_match:
            trailing.append(tag_match.group(1))
            caption = caption[: tag_match.start()].strip()
        cards.append(_render_card(is_bad, number, iframe_html, caption))

    grid_html = '<div class="example-grid">' + "".join(cards) + "</div>\n"
    if trailing:
        grid_html += "\n" + "\n".join(trailing) + "\n"

    heading_line = f"## {heading}"
    old_section = f"{heading_line}\n{body}"
    new_section = f"{heading_line}\n\n{grid_html}"
    return markdown.replace(old_section, new_section, 1)


def on_page_markdown(markdown, page, config, files):
    """Специфично для manual-2-etap/02-segments.md: блоки "**Пример N:** <iframe>...</iframe>" +
    картинка-кадр + подпись превращает в .example-grid/.example-card (карточка со встроенным
    плеером вместо статичного кадра — кадр становится избыточным, раз видео уже играбельно).
    Требует, чтобы embed_video_links.py уже отработал на этой странице раньше в конвейере хуков."""
    src_uri = page.file.src_uri.replace("\\", "/")
    if src_uri != TARGET_FILE:
        return markdown
    for heading in SECTION_HEADINGS:
        markdown = _transform_section(markdown, heading)
    return markdown
```

- [ ] **Step 4: Прогнать тесты**

Run: `cd site && python -m pytest hooks/tests/test_build_segment_examples.py -v`
Expected: 6 passed. Если `test_source_tag_kept_outside_cards` или другой тест падает из-за
точного формата пробелов/переносов — поправить `_SOURCE_TAG_RE`/сборку `grid_html` по
сообщению об ошибке (какая именно строка ожидалась и что получено) и перезапустить, пока все
6 не пройдут.

- [ ] **Step 5: Добавить CSS**

В `site/theme/extra.css` добавить (после блока Task 6):

```css
/* Сетка карточек примеров/антипримеров, собираемая build_segment_examples.py (Task 7) */
.example-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin: 1.4em 0;
}
@media (max-width: 820px) { .example-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 460px) { .example-grid { grid-template-columns: 1fr; } }
.example-card {
  border: 1px solid var(--card-line);
  border-radius: 10px;
  background: var(--gray-50);
  box-shadow: var(--card-shadow);
  display: flex;
  flex-direction: column;
}
.example-card .embedded-video {
  border-radius: 10px 10px 0 0;
  margin: 0;
}
.example-card .ec-body {
  padding: 10px 11px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.example-card .num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 19px;
  height: 19px;
  border-radius: 5px;
  background: var(--accent-bg);
  color: var(--accent-ink);
  font-family: 'Golos Text', sans-serif;
  font-size: .68rem;
  font-weight: 700;
}
.example-card.bad .num { background: var(--no-bg); color: var(--no-color); }
.example-card .ec-body p,
.example-card .ec-body div { font-size: .85rem; line-height: 1.5; color: var(--gray-600); margin: 0; }
.example-card .ec-body ul,
.example-card .ec-body ol { padding-left: 1.2em; margin: .3em 0 0; }
```

- [ ] **Step 6: Проверить файлы мануала и закоммитить**

```bash
git status --short manual-2-etap manual-3-etap
git add site/hooks/build_segment_examples.py site/hooks/tests/test_build_segment_examples.py site/theme/extra.css
git commit -m "Хук: блоки Пример N/Антипример N в 02-segments.md -> карточки .example-grid"
```

---

## Task 8: Хук точечных превью банка примеров у полей классификатора

**Files:**
- Create: `site/hooks/inject_example_previews.py`
- Test: `site/hooks/tests/test_inject_example_previews.py`

**Interfaces:**
- Consumes: `_section_utils.extract_section`, `_list_utils.split_list_items`.
- Produces: `inject_example_previews.on_page_markdown(markdown, page, config, files) -> str`.
  Должен идти **раньше** `embed_local_media.py`/`embed_video_links.py`/`group_media_lists.py` в
  конвейере — вставляет сырой markdown (необработанные ссылки), чтобы более поздние хуки сами
  превратили их в плеер и, если их 2+, сгруппировали в `.video-block`.

- [ ] **Step 1: Написать падающий тест**

Создать `site/hooks/tests/test_inject_example_previews.py`:

```python
from pathlib import Path

import pytest

from inject_example_previews import on_page_markdown, MAPPINGS

FIXTURES = Path(__file__).parent / "fixtures"


class FakeFile:
    def __init__(self, src_uri):
        self.src_uri = src_uri


class FakePage:
    def __init__(self, src_uri):
        self.file = FakeFile(src_uri)


@pytest.fixture(autouse=True)
def _docs_dir(monkeypatch):
    import inject_example_previews as mod

    monkeypatch.setattr(mod, "DOCS_DIR", FIXTURES)


def test_classifier_tempo_preview_inserted_after_anchor():
    target_md = (
        "- **Темп речи:** быстрый / медленный (цель по команде в целом — "
        "равномерное распределение).\n"
        "- **Язык и акценты:** русский / английский / другое.\n"
    )
    page = FakePage("manual-2-etap/04-classifier.md")
    result = on_page_markdown(target_md, page, None, None)
    assert "example1.mp4" in result
    assert "→ ещё" in result
    assert result.index("Темп речи:") < result.index("example1.mp4")
    assert result.index("example1.mp4") < result.index("Язык и акценты:")


def test_mapping_table_covers_expected_targets():
    targets = {m["target_file"] for m in MAPPINGS}
    assert "manual-2-etap/04-classifier.md" in targets
    assert "manual-3-etap/04-video-quality.md" in targets


def test_untouched_on_unrelated_page():
    md = "Обычный текст."
    page = FakePage("manual-2-etap/07-faq.md")
    assert on_page_markdown(md, page, None, None) == md
```

- [ ] **Step 2: Создать фикстуру-источник примеров**

Создать `site/hooks/tests/fixtures/manual-2-etap/11-example-library.md`:

```markdown
# Банк примеров по критериям

## Темп речи

- **Быстрая речь:** [пример 1](https://example.com/example1.mp4), [пример 2](https://example.com/example1b.mp4)
- **Средний темп:** [пример](https://example.com/example2.mp4)
- **Медленный темп:** [пример](https://example.com/example3.mp4)
```

- [ ] **Step 3: Прогнать, убедиться что падает**

Run: `cd site && python -m pytest hooks/tests/test_inject_example_previews.py -v`
Expected: FAIL, модуля `inject_example_previews` нет.

- [ ] **Step 4: Реализовать хук**

Создать `site/hooks/inject_example_previews.py`:

```python
import re
from pathlib import Path

from _section_utils import extract_section
from _list_utils import split_list_items

DOCS_DIR = Path(__file__).resolve().parents[2]

# Явная таблица соответствий: где на целевой странице вставить превью, и откуда его взять.
# position="after_line" — сразу после строки, содержащей anchor; "before_line" — прямо перед ней.
MAPPINGS = [
    {
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "- **Темп речи:** быстрый / медленный",
        "position": "after_line",
        "source_file": "manual-2-etap/11-example-library.md",
        "source_heading": "Темп речи",
        "max_items": 3,
    },
    {
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "- **Смена эмоций внутри одного ролика**",
        "position": "before_line",
        "source_file": "manual-2-etap/11-example-library.md",
        "source_heading": "Эмоции",
        "max_items": 3,
    },
    {
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "- **Группа данных:**",
        "position": "before_line",
        "source_file": "manual-2-etap/11-example-library.md",
        "source_heading": "Ракурс",
        "max_items": 2,
    },
    {
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "- **Освещение:**",
        "position": "before_line",
        "source_file": "manual-2-etap/11-example-library.md",
        "source_heading": "Диалоги и закадровый голос",
        "max_items": 2,
    },
    {
        "target_file": "manual-3-etap/04-video-quality.md",
        "anchor": '## Когда сразу «Битое» (не отвечая на вопросы классификатора)',
        "position": "after_line",
        "source_file": "manual-3-etap/07-example-library.md",
        "source_heading": "1. Размечено битое видео (хотя должно было быть отправлено в «битое»)",
        "max_items": 3,
    },
    {
        "target_file": "manual-3-etap/04-video-quality.md",
        "anchor": '## Когда отмечать «Артефакт», но всё равно отвечать на вопросы',
        "position": "after_line",
        "source_file": "manual-3-etap/07-example-library.md",
        "source_heading": "2. Наличие артефакта (не проставлен)",
        "max_items": 3,
    },
]


def _slugify(heading):
    slug = heading.lower().strip()
    slug = re.sub(r'[«»"\'()]', "", slug)
    slug = re.sub(r'[^\w\-]+', "-", slug, flags=re.UNICODE)
    return slug.strip("-")


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
    lines = ["", '<div markdown="1">', "**Примеры из банка:**", ""]
    lines.extend(preview_items)
    if remaining > 0:
        anchor = _slugify(mapping["source_heading"])
        link = f"{Path(mapping['source_file']).name}#{anchor}"
        lines.append(f"\n→ ещё {remaining} прим. в [банке примеров]({link})")
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
```

- [ ] **Step 5: Прогнать тест, убедиться что проходит**

Run: `cd site && python -m pytest hooks/tests/test_inject_example_previews.py -v`
Expected: 3 passed.

- [ ] **Step 6: Проверить якоря против реальных файлов**

```bash
cd "$(git rev-parse --show-toplevel)"
grep -n -- "- \*\*Темп речи:\* быстрый" manual-2-etap/04-classifier.md
grep -n -- "- \*\*Смена эмоций внутри одного ролика\*\*" manual-2-etap/04-classifier.md
grep -n -- "- \*\*Группа данных:\*\*" manual-2-etap/04-classifier.md
grep -n -- "- \*\*Освещение:\*\*" manual-2-etap/04-classifier.md
grep -n "## Когда сразу «Битое»" manual-3-etap/04-video-quality.md
grep -n "## Когда отмечать «Артефакт»" manual-3-etap/04-video-quality.md
grep -n "^### 1. Размечено битое видео" manual-3-etap/07-example-library.md
grep -n "^### 2. Наличие артефакта" manual-3-etap/07-example-library.md
grep -n "^## Темп речи" manual-2-etap/11-example-library.md
grep -n "^## Эмоции" manual-2-etap/11-example-library.md
grep -n "^## Ракурс" manual-2-etap/11-example-library.md
grep -n "^## Диалоги и закадровый голос" manual-2-etap/11-example-library.md
```

Каждая команда должна вернуть ровно одну строку. Если якорь в `MAPPINGS` не совпадает буква в
букву с реальным текстом (например, из-за переноса строки внутри длинного маркдауна) —
поправить `anchor`/`source_heading` в `site/hooks/inject_example_previews.py` на точную
подстроку из вывода `grep`, перезапустить тесты (Step 5).

- [ ] **Step 7: Проверить файлы мануала и закоммитить**

```bash
git status --short manual-2-etap manual-3-etap
git add site/hooks/inject_example_previews.py site/hooks/tests/test_inject_example_previews.py site/hooks/tests/fixtures/
git commit -m "Хук: точечные превью банка примеров у полей классификатора (04-classifier.md, 04-video-quality.md)"
```

---

## Task 9: Подключить все хуки в правильном порядке, PDF-профиль

Порядок в `hooks:` критичен: `inject_example_previews` (вставляет сырые ссылки) →
`hide_site_only_sections` → `embed_local_media` → `embed_video_links` → `group_media_lists` →
`build_segment_examples` (нужен уже встроенный iframe) → `build_compare_cards` →
`neutralize_excluded_links` (существующий, должен остаться последним, как раньше).

**Files:**
- Modify: `site/mkdocs.yml`
- Modify: `site/pdf/pdf-extra.css`

**Interfaces:** Не применимо (конфигурация).

- [ ] **Step 1: Обновить список хуков в `site/mkdocs.yml`**

Найти существующий блок:

```yaml
hooks:
  - hooks/wrap_source_tags.py
  - hooks/embed_local_media.py
  - hooks/neutralize_excluded_links.py
```

Заменить на:

```yaml
hooks:
  - hooks/wrap_source_tags.py
  - hooks/inject_example_previews.py
  - hooks/hide_site_only_sections.py
  - hooks/embed_local_media.py
  - hooks/embed_video_links.py
  - hooks/group_media_lists.py
  - hooks/build_segment_examples.py
  - hooks/build_compare_cards.py
  - hooks/neutralize_excluded_links.py
```

- [ ] **Step 2: Убедиться, что `mkdocs-pdf.yml` не переопределяет `hooks:`**

```bash
grep -n "hooks:" site/mkdocs-pdf.yml
```

Expected: пусто (ключ отсутствует — значит INHERIT из `mkdocs.yml` подхватит новый список
целиком, как и раньше для существующих трёх хуков).

- [ ] **Step 3: Нейтрализовать hover-zoom и уменьшение картинок в PDF-профиле**

В PDF нет наведения мышью, а компактность страниц там не нужна (PDF — полный
самостоятельный документ). Добавить в конец `site/pdf/pdf-extra.css`:

```css
/* Task 9 плана переупаковки: в PDF картинки/карточки остаются в обычном размере — там нет
   наведения курсора, а цель PDF — полнота, не компактность. */
.md-typeset img {
  max-width: 100% !important;
  max-height: none !important;
  box-shadow: none !important;
  cursor: default !important;
  transition: none !important;
}
.md-typeset img:hover { transform: none !important; }
.example-card .embedded-video,
.compare-card img,
.example-grid,
.video-grid {
  break-inside: avoid;
}
```

- [ ] **Step 4: Полная сборка сайта в строгом режиме**

```bash
cd site && mkdocs build --strict -f mkdocs.yml
```

Expected: `INFO - Documentation built...`, без WARNING/ERROR.

- [ ] **Step 5: Полная сборка PDF-профиля в строгом режиме**

```bash
cd site && mkdocs build --strict -f mkdocs-pdf.yml
```

Expected: `INFO - Documentation built...`, без WARNING/ERROR.

- [ ] **Step 6: Прогнать весь набор тестов хуков разом**

```bash
cd site && python -m pip install -r requirements-dev.txt && python -m pytest hooks/tests/ -v
```

Expected: все тесты из задач 1-8 проходят (порядка 30 тестов).

- [ ] **Step 7: Проверить файлы мануала и закоммитить**

```bash
git status --short manual-2-etap manual-3-etap
git add site/mkdocs.yml site/pdf/pdf-extra.css
git commit -m "Подключить новые хуки переупаковки контента в правильном порядке, PDF без сжатия картинок"
```

---

## Task 10: Живая проверка на реальном сайте и в PDF

Строгая сборка (Task 9) ловит только структурные ошибки MkDocs — не гарантирует, что регулярки
из задач 5-8 корректно распознали реальный, чуть неровный текст мануала. Эта задача — ручная
(глазами, не автотест), обязательна перед тем, как считать работу завершённой.

**Files:** нет изменений кода — только проверка.

- [ ] **Step 1: Поднять локальный сервер**

```bash
cd site && mkdocs serve -f mkdocs.yml
```

- [ ] **Step 2: Проверить `manual-2-etap/00-overview.md` и `manual-3-etap/00-overview.md`**

Открыть обе страницы в браузере. Убедиться, что разделов «История проекта...» и «Как читать
этот мануал» нет на странице, но соседние разделы («Порог качества...», «Обучение и входной
экзамен...», «Приватность») на месте.

- [ ] **Step 3: Проверить `manual-2-etap/02-segments.md` целиком**

Открыть страницу. Проверить:
- Раздел «Как выделять сегменты в интерфейсе» — таблица «Правильно/Неправильно» стала двумя
  карточками с картинками, при наведении картинка увеличивается.
- Раздел «Примеры (позитивные)» — сетка из 5 карточек, в каждой играющее видео (не картинка),
  при клике видео реально воспроизводится (проверить минимум 2 карточки, включая ту, что была
  с `?list=...` в исходной ссылке, и ту, что была `youtube.com/shorts`).
- В карточке «Пример 2» виден вложенный список («сегмент с плечами», «сегмент с появлением
  рук») — то есть многострочная подпись не потерялась.
- Раздел «Антипримеры» — отдельная сетка из 6 карточек, у каждой карточки красноватый номер
  (не такой, как у положительных примеров).
- Метки-источники (`[Инстр. ..., стр.5-7]`) не видны на странице (как и раньше, скрыты CSS).

- [ ] **Step 4: Проверить точечные превью классификатора**

Открыть `manual-2-etap/04-classifier.md`. Найти поле «Темп речи» в разделе «Уточнения по
конкретным полям» — сразу под ним должен быть компактный блок «Примеры из банка» с играющими
видео и ссылкой «→ ещё N прим. в банке примеров», ведущей на `11-example-library.md`. Проверить
клик по этой ссылке — должен вести на правильный якорь на странице банка примеров (браузер
прокручивает к разделу «Темп речи»). Повторить для «Эмоции», «Ракурс», «Диалоги/закадровый
голос».

Открыть `manual-3-etap/04-video-quality.md`. Найти разделы «Когда сразу «Битое»...» и «Когда
отмечать «Артефакт»...» — под заголовком должен быть блок превью со ссылкой на
`07-example-library.md`.

- [ ] **Step 5: Проверить, что банк примеров и качество видео 2 этапа тоже стали компактнее**

Открыть `manual-2-etap/11-example-library.md`, `manual-2-etap/03-video-quality.md` (разделы
«Артефакты, которые всё ещё допустимы», «Примеры «Битое»»), `manual-3-etap/07-example-library.md`.
Убедиться, что списки видео превратились в сетки `.video-block`, а не остались длинным
вертикальным списком плееров на всю ширину.

- [ ] **Step 6: Остановить сервер, проверить сборку PDF глазами**

Остановить `mkdocs serve` (Ctrl+C). Собрать и открыть PDF:

```bash
cd site && mkdocs build --strict -f mkdocs-pdf.yml
python pdf/render_pdf.py
```

Открыть получившийся PDF (путь — как в предыдущей сборке, `../avatar-manual-build/build-pdf/...`,
уточнить у `render_pdf.py`, если путь неочевиден). Проверить страницу «Сегменты»: разделы
«История проекта»/«Как читать» **присутствуют** (в отличие от сайта), метки-источников
**видны**, картинки не растянуты и не обрезаны безобразно.

- [ ] **Step 7: Финальная проверка целостности мануала и коммит (если были правки по ходу)**

```bash
git status --short manual-2-etap manual-3-etap
```

Expected: пусто. Если на шагах 2-6 находились расхождения и потребовались правки хуков —
закоммитить их (`git add site/... && git commit -m "..."`) с описанием конкретного найденного
и исправленного расхождения, по аналогии с тем, как фиксировались находки в
`docs/superpowers/plans/2026-08-06-avatar-manual-site.md`.

- [ ] **Step 8: Запушить**

```bash
git push
```

Проверить в GitHub Actions, что деплой прошёл зелёным, и открыть живой сайт
(`https://ekaterina-dl.github.io/avatar-manual/`) — повторить проверки Step 2-5 уже на
опубликованной версии, не только локально.

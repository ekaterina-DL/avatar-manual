# Мануал 3 этапа: визуальная система — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (Inline Execution — обоснование объёма см. в конце документа) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Перенести визуальную систему 2 этапа на 3 этап: статус-плашки в `02-open-questions.md`,
5 сквозных тематических эмодзи, и сетку карточек вместо голой таблицы на 18 примеров в
`03-common-mistakes.md`.

**Architecture:** Часть 1 (плашки) — расширение уже существующего хука `build_status_badges.py`
на второй файл + добавление источника-разметки (`- Статус: **X**`) в сам markdown. Часть 2
(эмодзи) — точечная правка текста, без кода, работает одинаково в PDF и на сайте. Часть 3
(таблица → карточки) — новый build-хук `build_verdict_examples.py` по образцу
`build_compare_cards.py`/`build_segment_examples.py`, плюс новый CSS.

**Tech Stack:** mkdocs-material, Python-Markdown (`md_in_html`), pytest, чистый CSS.

## Global Constraints

- Ни один заголовок (`#`/`##`/`###`) не переименовывается — эмодзи и правки текста идут только
  внутри тела раздела (bullet/строка таблицы/пункт списка), никогда в саму строку заголовка
  (якорная безопасность).
- Эмодзи-набор для части 2 — ровно 5 тем, три переиспользованы из 2 этапа (🚫 Битое, 🎥
  Тех. качество, ✂️ Склейки), две новые (📷 Тряска/движение камеры, 🐾 Мультики-антропоморфы) —
  не пересекаются с уже занятыми эмодзи 2 этапа (⏱️🔇✂️👤🎥🎭🚫).
- Классификация 4 пунктов `02-open-questions.md` на плашки — точно по таблице из дизайн-документа
  (`docs/superpowers/specs/2026-08-12-stage3-visual-system-design.md`), без импровизации.
- Цвета — только через существующие CSS-переменные (`--ok-color`/`--ok-bg`, `--no-color`/
  `--no-bg`, `--accent-ink`/`--accent-bg`) — новых токенов не вводится.
- После каждой задачи: `cd site/hooks && python -m pytest tests/ -q` должен остаться зелёным
  (действующие 114 тестов + новые из этой задачи).
- Build-diff обоих профилей (`mkdocs.yml`/`mkdocs-pdf.yml`) через `python -m mkdocs build
  --strict` не должен добавлять новых WARNING-строк.

---

## Task 1: Статус-плашки в `manual-3-etap/02-open-questions.md`

**Files:**
- Modify: `site/hooks/build_status_badges.py` (весь файл, 41 строка)
- Modify: `site/hooks/tests/test_build_status_badges.py` (добавить тесты в конец)
- Modify: `manual-3-etap/02-open-questions.md` (4 точечные вставки)

**Interfaces:**
- Produces: хук `build_status_badges.py` теперь применяется к множеству файлов
  `_TARGET_FILES = {"manual-2-etap/09-disputed-points.md", "manual-3-etap/02-open-questions.md"}`
  вместо одного жёстко заданного пути — используется Task 3 как референс того же паттерна
  (множество целевых файлов, а не один путь).

- [ ] **Шаг 1: Написать падающий тест на новый файл-цель**

Открыть `site/hooks/tests/test_build_status_badges.py`, добавить в конец файла:

```python

PAGE_STAGE3 = "manual-3-etap/02-open-questions.md"


def test_badge_applies_to_stage3_open_questions():
    page = FakePage(PAGE_STAGE3)
    config = FakeConfig("/repo/avatar-manual-build/build")
    src = "- Статус: **Не решено** — расшифровка не подтверждена.\n"
    result = on_page_markdown(src, page, config, None)
    assert '<span class="status-badge status-open">🔴 Не решено</span>' in result
    assert "— расшифровка не подтверждена." in result


def test_still_applies_to_stage2_disputed_points():
    page = FakePage(PAGE)
    config = FakeConfig("/repo/avatar-manual-build/build")
    src = "- Статус: **Решено** — пояснение.\n"
    result = on_page_markdown(src, page, config, None)
    assert '<span class="status-badge status-ok">🟢 Решено</span>' in result
```

- [ ] **Шаг 2: Запустить тест, убедиться, что он падает**

Run: `cd site/hooks && python -m pytest tests/test_build_status_badges.py::test_badge_applies_to_stage3_open_questions -v`
Expected: FAIL (хук пока проверяет только `manual-2-etap/09-disputed-points.md`, для
`manual-3-etap/02-open-questions.md` возвращает markdown без изменений — assert на
`status-badge` не находит совпадения).

- [ ] **Шаг 3: Расширить хук на множество целевых файлов**

Открыть `site/hooks/build_status_badges.py`, заменить весь файл на:

```python
import re

from _build_profile import is_pdf_build

_STATUS_RE = re.compile(
    r"^- Статус: \*\*(Решено|Частично решено|Не решено)\*\*",
    re.M,
)

_BADGE_CLASS = {
    "Решено": "status-ok",
    "Частично решено": "status-partial",
    "Не решено": "status-open",
}

_BADGE_EMOJI = {
    "Решено": "🟢",
    "Частично решено": "🟡",
    "Не решено": "🔴",
}

_TARGET_FILES = {
    "manual-2-etap/09-disputed-points.md",
    "manual-3-etap/02-open-questions.md",
}


def _render(match):
    label = match.group(1)
    css_class = _BADGE_CLASS[label]
    emoji = _BADGE_EMOJI[label]
    return f'- <span class="status-badge {css_class}">{emoji} {label}</span>'


def on_page_markdown(markdown, page, config, files):
    """Строка "- Статус: **Решено**/**Частично решено**/**Не решено**" (канонический словарь,
    см. шапку manual-2-etap/09-disputed-points.md, "Формат записи") превращается в цветную
    плашку. Матчит только сам ярлык в начале строки — текст пояснения после него (факты, даты,
    ссылки, цитаты) не трогает. Вложенные упоминания "Статус:" не в начале bullet-а не матчатся —
    regex заякорен на начало строки через re.M. Применяется к обоим файлам, использующим этот
    формат (manual-2-etap/09-disputed-points.md и manual-3-etap/02-open-questions.md, второй
    добавлен 12.08.2026) — сама regex-логика файл-агностична. PDF-профиль не трогаем: там
    остаётся обычный текст."""
    if is_pdf_build(config):
        return markdown
    if page.file.src_uri.replace("\\", "/") not in _TARGET_FILES:
        return markdown
    return _STATUS_RE.sub(_render, markdown)
```

- [ ] **Шаг 4: Запустить тесты, убедиться, что все проходят**

Run: `cd site/hooks && python -m pytest tests/test_build_status_badges.py -v`
Expected: все тесты `PASS`, включая новые из Шага 1.

- [ ] **Шаг 5: Добавить строки «Статус» в `manual-3-etap/02-open-questions.md`**

Текущий текст (конец раздела «Аббревиатура «ПНП»»):

```
критерий (когда именно «просто пикселизация» переходит в «ПНП») по-прежнему не даны явно.
**Нужно уточнить у заказчика прямым текстом.** `[Разметка ВК видео — ОС 3 этап 23.07]`

### «Пережатие» — нет чёткого количественного порога
```

Заменить на:

```
критерий (когда именно «просто пикселизация» переходит в «ПНП») по-прежнему не даны явно.
**Нужно уточнить у заказчика прямым текстом.** `[Разметка ВК видео — ОС 3 этап 23.07]`
- Статус: **Не решено** — расшифровка не подтверждена официально; заказчик использует термин на
  практике, но точный количественный критерий пока не дан.

### «Пережатие» — нет чёткого количественного порога
```

Текущий текст (конец раздела «Пережатие»):

```
что путаница на практике всё ещё вероятна. `[Памятка Аватар 3 этап; Вопросы по проекту (1ч) —
Чат исполнителей, апрель 2026]`

### Мелкое локальное движение фона — закрыто ✅
```

Заменить на:

```
что путаница на практике всё ещё вероятна. `[Памятка Аватар 3 этап; Вопросы по проекту (1ч) —
Чат исполнителей, апрель 2026]`
- Статус: **Частично решено** — качественное определение официально закреплено в переработанной
  памятке, но точный количественный порог «сколько ряби — уже пережатие» не дан.

### Мелкое локальное движение фона — закрыто ✅
```

Текущий текст (конец раздела «Мелкое локальное движение фона»):

```
но именно этот кейс отдельно не проверялся. `[Памятка Аватар 3 этап]`

### Несогласованность вердиктов по пиксельности (13–15.05.2026)
```

Заменить на:

```
но именно этот кейс отдельно не проверялся. `[Памятка Аватар 3 этап]`
- Статус: **Решено** — правило официально закреплено в переработанной памятке «АВАТАР 3 ЭТАП»
  (мелкие локальные шевеления фона — статичный, не динамичный фон).

### Несогласованность вердиктов по пиксельности (13–15.05.2026)
```

Текущий текст (последние 2 строки файла — конец раздела «Несогласованность вердиктов»):

```
косвенно показывает, что проблема шире и не ограничена одним периодом (13–15.05.2026) или одним
критерием (пиксельность). `[Разметка ВК видео — Вопросы 3 этап]`
```

Заменить на:

```
косвенно показывает, что проблема шире и не ограничена одним периодом (13–15.05.2026) или одним
критерием (пиксельность). `[Разметка ВК видео — Вопросы 3 этап]`
- Статус: **Не решено** — только гипотеза о причине (разногласие валидаторов), прямых официальных
  разъяснений от заказчика по конкретному эпизоду 13–15.05.2026 нет.
```

- [ ] **Шаг 6: Проверить заголовки/якоря не сдвинулись**

Run: `grep -n '^#' "manual-3-etap/02-open-questions.md"`
Expected: тот же список из 5 заголовков (1 `#` + 4 `###`), что и до правки.

- [ ] **Шаг 7: Коммит**

```bash
git add site/hooks/build_status_badges.py site/hooks/tests/test_build_status_badges.py manual-3-etap/02-open-questions.md
git commit -m "Статус-плашки для manual-3-etap/02-open-questions.md: расширяет build_status_badges.py на 2-й файл, добавляет 4 строки «Статус» (addendum дизайна визуальной системы 3 этапа, 12.08.2026)"
```

---

## Task 2: Сквозные тематические эмодзи (5 тем, 5 файлов, 9 вставок)

**Files:**
- Modify: `manual-3-etap/04-video-quality.md` (3 вставки: 🚫, 🎥, ✂️)
- Modify: `manual-3-etap/03-common-mistakes.md` (2 вставки: 🚫, 📷)
- Modify: `manual-3-etap/02-open-questions.md` (1 вставка: 🎥)
- Modify: `manual-3-etap/01-classifier.md` (2 вставки: ✂️, 📷)
- Modify: `manual-3-etap/06-general-requirements.md` (1 вставка: 🐾)

**Interfaces:** нет — чистая правка текста, не затрагивает код.

- [ ] **Шаг 1: 🚫 Битое — `04-video-quality.md`, таблица «Логика разметки»**

Текущий текст:

```
| Действие | Что делать |
|---|---|
| ☑ Битое | На вопросы отвечать **не нужно** |
| ☑ Артефакт | **Нужно ответить** на вопросы |
| ☑ Рамка | Отметить поле «рамка» и ответить на вопросы |
```

Заменить на:

```
| Действие | Что делать |
|---|---|
| ☑ 🚫 Битое | На вопросы отвечать **не нужно** |
| ☑ 🎥 Артефакт | **Нужно ответить** на вопросы |
| ☑ Рамка | Отметить поле «рамка» и ответить на вопросы |
```

(Одновременно с 🚫 здесь же ставится и 🎥 «Тех. качество/артефакт» — Шаг 3 ниже её не дублирует
для этого файла, только для другого.)

- [ ] **Шаг 2: ✂️ Склейки — `04-video-quality.md`, список «Когда сразу «Битое»»**

Текущий текст:

```
- 3 и более монтажных склейки на видео (1-2 — допустимо).
```

Заменить на:

```
- ✂️ 3 и более монтажных склейки на видео (1-2 — допустимо).
```

- [ ] **Шаг 3: 🚫 Битое — `03-common-mistakes.md`, интро таблицы калибровки**

Текущий текст:

```
Самая частая ошибка проекта — «не отмечен артефакт» (см. таблицу выше, 82 случая). Ниже —
конкретные примеры, где команда отправляла видео в «битое», а заказчик снижал вердикт до
«артефакт», и наоборот — примеры именно «битого» уровня. Дистанция съёмки и темнота **сами по
себе не критерий** — важно, теряются ли из-за них черты лица/цвет.
```

Заменить на:

```
Самая частая ошибка проекта — «не отмечен артефакт» (см. таблицу выше, 82 случая). 🚫 Ниже —
конкретные примеры, где команда отправляла видео в «битое», а заказчик снижал вердикт до
«артефакт», и наоборот — примеры именно «битого» уровня. Дистанция съёмки и темнота **сами по
себе не критерий** — важно, теряются ли из-за них черты лица/цвет.
```

- [ ] **Шаг 4: 📷 Тряска/движение камеры — `03-common-mistakes.md`, таблица частых ошибок**

Текущий текст:

```
| Камера (тряска vs статика) | 36 | Выбрана «статичная камера», хотя присутствует тряска; тряской отмечены плавные движения. |
```

Заменить на:

```
| 📷 Камера (тряска vs статика) | 36 | Выбрана «статичная камера», хотя присутствует тряска; тряской отмечены плавные движения. |
```

- [ ] **Шаг 5: 🎥 Тех. качество — `02-open-questions.md`, раздел «ПНП»**

Текущий текст:

```
В переписке команда неоднократно использует «ПНП» как самостоятельный вердикт наравне с «арт»
(артефакт) и «бит» (битое) — например: «арт согл, динамичный фон, арт, ПНП». Расшифровка нигде
```

Заменить на:

```
🎥 В переписке команда неоднократно использует «ПНП» как самостоятельный вердикт наравне с «арт»
(артефакт) и «бит» (битое) — например: «арт согл, динамичный фон, арт, ПНП». Расшифровка нигде
```

- [ ] **Шаг 6: ✂️ Склейки — `01-classifier.md`, вопрос 6**

Текущий текст:

```
6. **Непрерывная ли сцена без монтажных склеек** (выбрать по факту): continuous / contains_cut.
```

Заменить на:

```
6. ✂️ **Непрерывная ли сцена без монтажных склеек** (выбрать по факту): continuous / contains_cut.
```

- [ ] **Шаг 7: 📷 Тряска/движение камеры — `01-classifier.md`, вопрос 12**

Текущий текст:

```
12. **Смена ракурса/зум/панорамирование во время речи** (выбрать по факту): static (камера
    закреплена) / moving (плавное движение) / shaky (тряска).
```

Заменить на:

```
12. 📷 **Смена ракурса/зум/панорамирование во время речи** (выбрать по факту): static (камера
    закреплена) / moving (плавное движение) / shaky (тряска).
```

- [ ] **Шаг 8: 🐾 Мультики-антропоморфы — `06-general-requirements.md`**

Текущий текст:

```
- **Мультики (антропоморфы)** размечаются по общим правилам, но пол/возраст/эмоции у них могут
  быть оценены субъективно — не всегда получается точно опознать эти характеристики. Берём в
  разметку, если персонаж подходит под требования ТЗ — подтверждено заказчиком несколько раз.
```

Заменить на:

```
- 🐾 **Мультики (антропоморфы)** размечаются по общим правилам, но пол/возраст/эмоции у них могут
  быть оценены субъективно — не всегда получается точно опознать эти характеристики. Берём в
  разметку, если персонаж подходит под требования ТЗ — подтверждено заказчиком несколько раз.
```

- [ ] **Шаг 9: Проверить заголовки/якоря во всех 5 файлов не сдвинулись**

Run:
```bash
grep -n '^#' "manual-3-etap/04-video-quality.md"
grep -n '^#' "manual-3-etap/03-common-mistakes.md"
grep -n '^#' "manual-3-etap/02-open-questions.md"
grep -n '^#' "manual-3-etap/01-classifier.md"
grep -n '^#' "manual-3-etap/06-general-requirements.md"
```
Expected: во всех 5 — тот же список заголовков и в том же порядке, что и до правки (эмодзи нигде
не попал в строку `#`/`##`/`###`).

- [ ] **Шаг 10: Build-diff (сайт) — эмодзи не ломают сборку**

```bash
cd site
git stash
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict --config-file mkdocs.yml 2>&1 | tail -n 40 > /tmp/before-emoji.txt
git stash pop
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict --config-file mkdocs.yml 2>&1 | tail -n 40 > /tmp/after-emoji.txt
diff /tmp/before-emoji.txt /tmp/after-emoji.txt
```

Expected: exit 0 на обоих билдах, `diff` не показывает новых `WARNING`-строк (только время
сборки может отличаться).

- [ ] **Шаг 11: Коммит**

```bash
git add manual-3-etap/04-video-quality.md manual-3-etap/03-common-mistakes.md manual-3-etap/02-open-questions.md manual-3-etap/01-classifier.md manual-3-etap/06-general-requirements.md
git commit -m "5 сквозных тематических эмодзи в manual-3-etap/ (🚫 Битое, 🎥 Тех. качество, ✂️ Склейки — переиспользованы из 2 этапа; 📷 Тряска камеры, 🐾 Мультики-антропоморфы — новые), addendum дизайна визуальной системы 3 этапа, 12.08.2026"
```

---

## Task 3: Хук `build_verdict_examples.py` — таблица калибровки → карточки

**Files:**
- Create: `site/hooks/build_verdict_examples.py`
- Create: `site/hooks/tests/test_build_verdict_examples.py`
- Modify: `site/theme/extra.css` (добавить в конец, после блока волны градиентной шкалы/декодед-
  исходов, добавленного 12.08.2026 — новые правила `.example-card.good`, `.example-card.warn`,
  `.ec-verdict` и её цветовые модификаторы)
- Modify: `site/mkdocs.yml` (зарегистрировать новый хук в списке `hooks:`)

**Interfaces:**
- Consumes: HTML `<video>`-теги, уже вставленные хуком `embed_local_media.py` (обязан выполняться
  раньше в списке `hooks:`), и CSS-классы `.example-grid`/`.example-card` (уже существуют, из
  волны переупаковки сайта 07.08.2026).
- Produces: CSS-классы `.example-card.good`, `.example-card.warn` (плюс уже существующий
  `.example-card.bad`) и `.ec-verdict` — используются в HTML, который генерирует этот хук.

- [ ] **Шаг 1: Написать падающие тесты**

Создать `site/hooks/tests/test_build_verdict_examples.py`:

```python
from build_verdict_examples import on_page_markdown
from _render_helpers import render_html

VIDEO_1 = ('<video controls preload="metadata" style="max-width:100%">'
           '<source src="https://a.mp4" type="video/mp4">видео</video>')
VIDEO_2 = ('<video controls preload="metadata" style="max-width:100%">'
           '<source src="https://b.mp4" type="video/mp4">видео</video>')
VIDEO_3 = ('<video controls preload="metadata" style="max-width:100%">'
           '<source src="https://c.mp4" type="video/mp4">видео</video>')

TABLE_MD = (
    "Текст перед таблицей.\n\n"
    "| Вердикт заказчика | Признак | Пример |\n"
    "|---|---|---|\n"
    f"| Битое | Критичная пикселизация | {VIDEO_1} |\n"
    f"| Подходящее видео | Хорошее качество | {VIDEO_2} |\n"
    f"| Артефакт (не битое) | **Небольшой** дефект | {VIDEO_3} |\n"
    "\n"
    "Текст после таблицы.\n"
)


class FakeFile:
    src_uri = "manual-3-etap/03-common-mistakes.md"


class FakePage:
    file = FakeFile()


class FakeSiteDir:
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return self._value


class FakeConfig(dict):
    def __init__(self, site_dir):
        super().__init__()
        self.site_dir = FakeSiteDir(site_dir)


SITE_CONFIG = FakeConfig("/repo/avatar-manual-build/build")
PDF_CONFIG = FakeConfig("/repo/avatar-manual-build/build-pdf")


def test_table_becomes_example_grid_with_three_verdicts():
    result = on_page_markdown(TABLE_MD, FakePage(), SITE_CONFIG, None)
    assert '<div class="example-grid" markdown="1">' in result
    assert '<div class="example-card bad" markdown="1">' in result
    assert '<div class="example-card good" markdown="1">' in result
    assert '<div class="example-card warn" markdown="1">' in result
    assert result.count('<div class="example-card') == 3


def test_verdict_tags_present():
    result = on_page_markdown(TABLE_MD, FakePage(), SITE_CONFIG, None)
    assert "🚫 Битое" in result
    assert "✅ Подходящее" in result
    assert "🟡 Артефакт" in result


def test_video_tags_preserved():
    result = on_page_markdown(TABLE_MD, FakePage(), SITE_CONFIG, None)
    assert VIDEO_1 in result
    assert VIDEO_2 in result
    assert VIDEO_3 in result


def test_feature_text_preserved():
    result = on_page_markdown(TABLE_MD, FakePage(), SITE_CONFIG, None)
    assert "Критичная пикселизация" in result
    assert "Хорошее качество" in result
    assert "**Небольшой** дефект" in result


def test_surrounding_text_preserved():
    result = on_page_markdown(TABLE_MD, FakePage(), SITE_CONFIG, None)
    assert "Текст перед таблицей." in result
    assert "Текст после таблицы." in result


def test_untouched_on_other_pages():
    class OtherFile:
        src_uri = "manual-3-etap/07-example-library.md"

    class OtherPage:
        file = OtherFile()

    assert on_page_markdown(TABLE_MD, OtherPage(), SITE_CONFIG, None) == TABLE_MD


def test_noop_on_pdf_build():
    result = on_page_markdown(TABLE_MD, FakePage(), PDF_CONFIG, None)
    assert result == TABLE_MD


def test_table_without_matching_header_untouched():
    md = "| Другая | Таблица |\n|---|---|\n| a | b |\n"
    assert on_page_markdown(md, FakePage(), SITE_CONFIG, None) == md


def test_rendered_html_bold_in_feature_becomes_strong():
    result = on_page_markdown(TABLE_MD, FakePage(), SITE_CONFIG, None)
    html = render_html(result)
    assert 'markdown="1"' not in html
    assert "<strong>Небольшой</strong> дефект" in html
```

- [ ] **Шаг 2: Запустить тесты, убедиться, что все падают**

Run: `cd site/hooks && python -m pytest tests/test_build_verdict_examples.py -v`
Expected: `ModuleNotFoundError: No module named 'build_verdict_examples'` (файл ещё не создан).

- [ ] **Шаг 3: Создать хук**

Создать `site/hooks/build_verdict_examples.py`:

```python
import re

from _build_profile import is_pdf_build

TARGET_FILE = "manual-3-etap/03-common-mistakes.md"

_HEADER_RE = re.compile(
    r'\| Вердикт заказчика \| Признак \| Пример \|\n'
    r'\|[-: ]+\|[-: ]+\|[-: ]+\|\n'
)
_ROW_RE = re.compile(
    r'\| (Битое|Подходящее видео|Артефакт \(не битое\)) \| (.+) \| (.+) \|'
)

_CARD_CLASS = {
    "Битое": "bad",
    "Подходящее видео": "good",
    "Артефакт (не битое)": "warn",
}

_VERDICT_TAG = {
    "Битое": "🚫 Битое",
    "Подходящее видео": "✅ Подходящее",
    "Артефакт (не битое)": "🟡 Артефакт",
}


def _render_card(verdict, feature, video_html):
    card_class = f"example-card {_CARD_CLASS[verdict]}"
    tag = _VERDICT_TAG[verdict]
    return (
        f'<div class="{card_class}" markdown="1">\n'
        f'{video_html}\n'
        '<div class="ec-body" markdown="1">\n'
        f'<span class="ec-verdict">{tag}</span>\n'
        "\n"
        f'{feature}\n'
        "\n"
        "</div>\n"
        "</div>"
    )


def _transform(markdown):
    header_match = _HEADER_RE.search(markdown)
    if not header_match:
        return markdown
    rest = markdown[header_match.end():]
    cards = []
    consumed = 0
    for line in rest.splitlines(keepends=True):
        row_match = _ROW_RE.fullmatch(line.strip())
        if not row_match:
            break
        verdict, feature, video_html = row_match.groups()
        cards.append(_render_card(verdict, feature.strip(), video_html.strip()))
        consumed += len(line)
    if not cards:
        return markdown
    table_text = markdown[header_match.start():header_match.end() + consumed]
    grid_html = '<div class="example-grid" markdown="1">\n' + "\n".join(cards) + "\n</div>"
    return markdown.replace(table_text, grid_html, 1)


def on_page_markdown(markdown, page, config, files):
    """Таблица "| Вердикт заказчика | Признак | Пример |" в manual-3-etap/03-common-mistakes.md
    (раздел "Битое или артефакт калибровка по пикселизации и цвету", 18 строк) превращается в
    .example-grid/.example-card с цветным тегом-вердиктом вместо голой ссылки на видео в ячейке.
    Матчит таблицу по заголовку колонок (устойчиво к правкам окружающей прозы — тот же принцип,
    что в build_compare_cards.py), а не по всему разделу целиком, поэтому вступительный и
    заключительный абзацы раздела остаются нетронутыми текстом снаружи новой сетки. Должен
    выполняться после hooks/embed_local_media.py — в колонке "Пример" на входе уже готовый
    <video>-тег, а не голая ссылка на .mp4. PDF-профиль — no-op (тот же принцип, что в
    build_segment_examples.py): в печати таблица остаётся обычной, а ссылка на видео уже
    кликабельна как текст через embed_local_media.py (эта часть не зависит от профиля)."""
    if is_pdf_build(config):
        return markdown
    src_uri = page.file.src_uri.replace("\\", "/")
    if src_uri != TARGET_FILE:
        return markdown
    return _transform(markdown)
```

- [ ] **Шаг 4: Запустить тесты, убедиться, что все проходят**

Run: `cd site/hooks && python -m pytest tests/test_build_verdict_examples.py -v`
Expected: все 9 тестов `PASS`.

- [ ] **Шаг 5: Зарегистрировать хук в `site/mkdocs.yml`**

Текущий текст (блок `hooks:`):

```yaml
  - hooks/build_segment_examples.py
  - hooks/build_compare_cards.py
  - hooks/build_dispute_flow.py
```

Заменить на:

```yaml
  - hooks/build_segment_examples.py
  - hooks/build_compare_cards.py
  - hooks/build_verdict_examples.py
  - hooks/build_dispute_flow.py
```

- [ ] **Шаг 6: Добавить CSS для новых модификаторов карточки и тега-вердикта**

Открыть `site/theme/extra.css`, перейти в конец файла (после блока `.decision-outcome`,
добавленного волной градиентной шкалы 12.08.2026), добавить:

```css

/* Карточки-вердикты таблицы калибровки (manual-3-etap/03-common-mistakes.md), собираемые
   build_verdict_examples.py — расширяет уже существующие .example-grid/.example-card двумя
   новыми модификаторами (good/warn, третий — bad — уже существовал) и тегом-вердиктом
   .ec-verdict (вместо маленького кружка-номера .num, который тут неуместен — не индекс примера,
   а сам вердикт). См. addendum 12.08.2026 к
   docs/superpowers/specs/2026-08-12-stage3-visual-system-design.md */
.example-card .ec-verdict {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-family: 'Golos Text', sans-serif;
  font-size: .74rem;
  font-weight: 700;
  white-space: nowrap;
}
.example-card.good .ec-verdict { background: var(--ok-bg); color: var(--ok-color); }
.example-card.bad .ec-verdict { background: var(--no-bg); color: var(--no-color); }
.example-card.warn .ec-verdict { background: var(--accent-bg); color: var(--accent-ink); }
```

- [ ] **Шаг 7: Build-diff (сайт) — реальная таблица становится сеткой**

```bash
cd site
git stash
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict --config-file mkdocs.yml 2>&1 | tail -n 40 > /tmp/before-verdict.txt
git stash pop
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict --config-file mkdocs.yml 2>&1 | tail -n 40 > /tmp/after-verdict.txt
diff /tmp/before-verdict.txt /tmp/after-verdict.txt
```

Expected: exit 0 на обоих билдах, `diff` не показывает новых `WARNING`.

- [ ] **Шаг 8: Проверить собранный HTML сайта — 18 карточек, 3 вердикта**

```bash
F=$(find "/d/ПРОЕКТЫ с Ai/avatar-manual-build/build/manual-3-etap/03-common-mistakes" -iname "index.html")
grep -o 'class="example-card good"' "$F" | wc -l
grep -o 'class="example-card bad"' "$F" | wc -l
grep -o 'class="example-card warn"' "$F" | wc -l
```

Expected: `good` = 7, `bad` = 10, `warn` = 1 (сумма 18, см. подсчёт в дизайн-документе).

- [ ] **Шаг 9: Build-diff — PDF-профиль (хук должен быть no-op, таблица остаётся таблицей)**

```bash
cd site
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict --config-file mkdocs-pdf.yml 2>&1 | tail -n 40
F=$(find "/d/ПРОЕКТЫ с Ai/avatar-manual-build/build-pdf/manual-3-etap/03-common-mistakes" -iname "index.html")
grep -c 'example-card' "$F"
```

Expected: build exit 0, без новых WARNING; вторая команда — `0` (на PDF таблица осталась
таблицей, карточек нет вообще).

- [ ] **Шаг 10: Финальный прогон полного набора тестов**

Run: `cd site/hooks && python -m pytest tests/ -q`
Expected: `123 passed` (114 существующих + 9 новых из этой задачи; Task 1 не добавлял новых
тестов сверх 2, см. пересчёт ниже¹).

¹ Проверка счёта: было 114. Task 1 добавил 2 теста (114+2=116). Task 3 добавляет 9 (116+9=125).
Если итоговое число не совпадает — не блокер, просто пересчитать по факту по выводу pytest, это
не проверка на конкретное число ради самого числа, а сверка, что ни один тест не пропал и не
упал.

- [ ] **Шаг 11: Коммит**

```bash
git add site/hooks/build_verdict_examples.py site/hooks/tests/test_build_verdict_examples.py site/mkdocs.yml site/theme/extra.css
git commit -m "Новый хук build_verdict_examples.py: таблица калибровки на 18 примеров в manual-3-etap/03-common-mistakes.md → сетка карточек с цветным вердиктом (Битое/Подходящее/Артефакт), addendum дизайна визуальной системы 3 этапа, 12.08.2026"
```

---

## Self-Review (выполнено при написании плана)

1. **Покрытие спеки:** все 3 части дизайн-документа покрыты — Часть 1 → Task 1, Часть 2 →
   Task 2, Часть 3 → Task 3. Раздел «Что сознательно не входит» спеки не требует задач.
2. **Плейсхолдеры:** просканировано — нет TBD/TODO, весь код/CSS/markdown дан целиком, команды
   проверки — с точным ожидаемым выводом (кроме итогового счётчика тестов в Шаге 10 Task 3, где
   явно объяснено, почему точное число — сверка, а не жёсткое требование).
3. **Согласованность имён:** `_TARGET_FILES` (Task 1) и `TARGET_FILE`/`_CARD_CLASS`/
   `_VERDICT_TAG` (Task 3) используются одинаково в определении хука и в тестах. CSS-классы
   `.example-card.good`/`.warn`/`.ec-verdict`, объявленные в Task 3 Шаг 6, — те же строки, что
   использует хук в Шаге 3. Тесты Task 3 используют ту же структуру `FakePage`/`FakeConfig`, что
   уже применяется в `test_build_segment_examples.py` (переиспользован проверенный паттерн, не
   изобретён новый).

## Порядок и независимость задач

Все 3 задачи независимы друг от друга (разные файлы, кроме `pytest`/build-diff, которые просто
накопительно растут) — можно выполнять в любом порядке, но естественный порядок (как в
дизайн-документе) — Task 1 → Task 2 → Task 3, от простого к сложному.

## Обоснование Inline Execution

Как и в предыдущей волне (градиентная шкала/блок-схема «Сегмент/Битое», тот же день), объём
небольшой (1 новый хук + 1 новый тестовый файл + CSS + точечные правки текста в 6 файлах) и
контроллер уже держит в контексте все нужные файлы (провёл разведку — прочитал все 8 файлов
`manual-3-etap/` целиком перед дизайном), включая референсные хуки (`build_compare_cards.py`,
`build_segment_examples.py`) — повторное чтение фреш-сабагентом того же контекста было бы чистым
накладным расходом без выигрыша в качестве.

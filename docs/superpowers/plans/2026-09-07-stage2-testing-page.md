# Страница тестирования по 2 этапу — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить в сайт-мануал отдельную акцентную страницу самопроверки: 15 вопросов с таймером 60 с, вопросы собираются на сборке из актуального контента мануала 2 этапа (+ ручной блок), итоги уходят в Google-таблицу.

**Architecture:** Новая страница MkDocs `manual-2-etap/07-testirovanie.md` + top-level раздел меню. Python-хук `build_quiz_bank.py` на сборке парсит структурированные места мануала 2 этапа (кроме `00-overview.md`) и ручной `_quiz-manual.yml`, склеивает банк вопросов и вставляет его в страницу как `<script id="quiz-bank" type="application/json">`. Квиз — ванильный JS (`site/theme/quiz.js` + `quiz.css`), без фреймворков, по образцу существующего `compare-tables.js`. Отправка результата — один `fetch` POST на веб-приложение Google Apps Script.

**Tech Stack:** Python 3.12, MkDocs 1.6 + mkdocs-material, PyYAML (уже транзитивно, фиксируем явно), pytest (`site/hooks/tests/`), ванильный JS/CSS, Google Apps Script.

## Global Constraints

- Отвечать и писать комментарии/тексты — **по-русски** (глобальное правило пользователя).
- **Коммитить и пушить сразу** после каждой завершённой задачи (`git add … && git commit && git push`). Не ждать отдельного запроса.
- Работаем прямо в `main` (в этом репозитории так принято), без worktree.
- Перед удалением любых файлов — явное подтверждение пользователя. В этом плане удалений нет.
- `nav` и `exclude_docs` при `INHERIT` в mkdocs 1.6.1 **заменяются целиком**, а не дополняются. Любая правка этих ключей идёт синхронно в `site/mkdocs.yml` и `site/mkdocs-public.yml`; рядом — комментарий-напоминание.
- **Публичная сборка (`site/mkdocs-public.yml`) — это то, что деплоится** на GitHub Pages. Страница теста обязана быть в её `nav`.
- Мобильную ширину не проверяем — мануал только для десктопа.
- `00-overview.md` **не входит** в источники вопросов (список целевых файлов в хуке — явный).
- Вариантов ответа у любого вопроса — **не менее 3**, верный — ровно один.
- Ничего не «додумываем»: вопрос берётся из мануала, только если правильный ответ там задан явно (жирным значением, заголовком-категорией, числом в `keyfacts`). Иначе источник пропускается.
- Команды сборки — с UTF-8 окружением: `cd site && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict [-f <config>]`.
- Тесты хуков: `cd site/hooks && python -m pytest tests/ -q`. Базовое число до начала работ — **140 passed**.

---

## Структура файлов

| Файл | Статус | Ответственность |
|---|---|---|
| `manual-2-etap/07-testirovanie.md` | создать | Вступление (markdown) + контейнер `<div id="quiz-root">` + маркер `<!-- QUIZ-BANK -->` + `<noscript>`. |
| `manual-2-etap/_quiz-manual.yml` | создать | Ручной блок вопросов (правила без машинной структуры). Не публикуется (в `exclude_docs`), но коммитится. |
| `site/hooks/build_quiz_bank.py` | создать | Хук `on_page_markdown`: читает соседние `.md`, извлекает вопросы (источники A–E), мёржит `_quiz-manual.yml` (F), собирает банк, вставляет `<script id="quiz-bank">` вместо маркера. No-op на PDF (ставит короткую заметку). |
| `site/hooks/tests/test_build_quiz_bank.py` | создать | pytest на все экстракторы и сборку банка (образец — `test_build_segment_examples.py`). |
| `site/theme/quiz-config.js` | создать | `window.QUIZ_CONFIG = { endpoint, token, passPercent }`. |
| `site/theme/quiz.js` | создать | Логика: гейт по ФИО → сборка набора 15 → вопрос+таймер → разбор → результат → отправка. Активируется только при `#quiz-root`. |
| `site/theme/quiz.css` | создать | Стили всех экранов квиза + акцентный пункт меню. |
| `site/quiz/apps-script.gs` | создать | Код Google Apps Script (`doPost`). |
| `docs/quiz-apps-script.md` | создать | Пошаговая инструкция публикации скрипта + smoke-тест. |
| `site/mkdocs.yml` | правка | top-level раздел меню; `quiz.css` в `extra_css`; `quiz-config.js`+`quiz.js` в `extra_javascript`; `build_quiz_bank.py` в `hooks:`; `_quiz-manual.yml` в `exclude_docs`. |
| `site/mkdocs-public.yml` | правка | тот же `nav` (с разделом) и `exclude_docs` (с `_quiz-manual.yml`). |
| `site/mkdocs-pdf.yml` | правка | добавить страницу в `plugins → print-site → exclude`. |
| `site/requirements.txt` | правка | явный `pyyaml>=6` с комментарием. |

---

## Категории вопросов и целевой состав набора (общая справка для Задач 8–9)

| Код | Источник | Цель в наборе | Минимум |
|---|---|---|---|
| `A` | Поля классификатора по видео (`04-classifier.md`) | 5 | 3 |
| `B` | «Битое»/дефекты (`11-example-library.md`, `05b-what-not-to-label.md`) | 3 | 2 |
| `C` | Позитив/антипримеры (`05-what-to-label.md`) | 2 | 1 |
| `DE` | Числа и правила (`02-segments.md`, `04-classifier.md`) | 2 | 1 |
| `F` | Ручной блок (`_quiz-manual.yml`) | 3 | 2 |

Сумма целей = 15. Потолок на одну `topic` в наборе — 6.

Формат одного вопроса в банке (JSON):

```json
{
  "id": "A-preobladayushchij-rakurs-1a2b3c4d",
  "category": "A",
  "topic": "Преобладающий ракурс",
  "question": "Определите по видео: преобладающий ракурс.",
  "videoUrl": "https://…mp4",
  "videoKind": "mp4",
  "videoStart": 6.48,
  "options": ["Анфас", "Полуоборот (3/4)", "Профиль"],
  "answer": 0,
  "review": { "title": "Классификатор", "url": "04-classifier.md#4-преобладающий-ракурс" }
}
```

- `options[0]` — всегда верный, `answer` всегда `0` в банке; порядок вариантов перемешивает JS при показе.
- `videoUrl` может отсутствовать (текстовый вопрос). `videoKind ∈ {"mp4","vk","youtube"}`. `videoStart` — секунды или отсутствует.
- `id` авто-вопроса: `f"{category}-{slug(topic)}-{sha1(dedup_key)[:8]}"`. `id` ручного — из YAML-поля `id`.

---

### Task 1: Страница, раздел меню, конфиг, акцент в CSS

**Files:**
- Create: `manual-2-etap/07-testirovanie.md`
- Create: `site/theme/quiz-config.js`
- Create: `site/theme/quiz.css`
- Modify: `site/mkdocs.yml` (`nav`, `extra_css`, `extra_javascript`)
- Modify: `site/mkdocs-public.yml` (`nav`)

**Interfaces:**
- Produces: страница по URL `/manual-2-etap/07-testirovanie/`; глобальный `window.QUIZ_CONFIG`; CSS-класс акцента на пункте меню; пустой контейнер `#quiz-root` и маркер `<!-- QUIZ-BANK -->` в теле страницы (для Задачи 2).

- [ ] **Step 1: Создать `manual-2-etap/07-testirovanie.md`**

```markdown
# Тестирование по 2 этапу

!!! warning "Перед началом"
    Перед прохождением этого тестирования **обязательно** ознакомьтесь со всем мануалом по
    2 этапу — все разделы слева, кроме [«Обзор проекта»](00-overview.md). Вопросы собираются
    из актуального содержания мануала и охватывают сегменты, классификатор, критерии «Что
    размечаем / не размечаем» и частые ошибки.

**Как устроен тест**

- 15 вопросов, собираются заново при каждом прохождении — два одинаковых теста подряд не выпадут.
- На каждый вопрос — 60 секунд. Не успели ответить — вопрос засчитывается как неверный и тест
  идёт дальше. Отсчёт для вопросов с видео начинается, когда ролик готов к просмотру.
- После ответа сразу видно, верно или нет; при ошибке подсвечивается правильный вариант.
  Дальше — по кнопке «Далее».
- В конце — процент, число верных ответов, вердикт и список разделов мануала, которые стоит
  повторить.

<div id="quiz-root" markdown="0"><!-- Содержимое рисует site/theme/quiz.js --></div>

<noscript>
Для прохождения тестирования включите JavaScript в браузере.
</noscript>

<!-- QUIZ-BANK -->
```

- [ ] **Step 2: Создать `site/theme/quiz-config.js`**

```javascript
// Конфиг тестирования. Значения безопасно держать в открытом виде: endpoint веб-приложения
// Apps Script всё равно виден в исходниках страницы. token — лёгкая защита от случайных
// посторонних отправок, не секрет.
window.QUIZ_CONFIG = {
  // URL веб-приложения Google Apps Script вида https://script.google.com/macros/s/…/exec
  // Заполняется после публикации скрипта (см. docs/quiz-apps-script.md). Пока пусто —
  // квиз работает, но на экране результата показывает «отправка не настроена».
  endpoint: "",
  // Тот же токен, что зашит в apps-script.gs (константа TOKEN).
  token: "avatar-stage2-quiz",
  // Порог вердикта «Сдано», проценты.
  passPercent: 80
};
```

- [ ] **Step 3: Создать `site/theme/quiz.css` с акцентом пункта меню (остальные стили добавят Задачи 9–12)**

```css
/* ==== Тестирование по 2 этапу ==== */

/* Акцент на пункте меню «Тестирование по 2 этапу» — и во вкладках сверху, и в левом
   оглавлении. Тема Material не даёт штатного способа выделить один пункт, поэтому таргет —
   по href последнего сегмента URL. Совпадает и для .md-tabs__link (вкладки), и для
   .md-nav__link (сайдбар). */
.md-tabs__link[href$="/manual-2-etap/07-testirovanie/"],
.md-nav__link[href$="/manual-2-etap/07-testirovanie/"] {
  font-weight: 700;
}
.md-nav__link[href$="/manual-2-etap/07-testirovanie/"] {
  color: var(--md-accent-fg-color, #ff6f00);
}
.md-nav__link[href$="/manual-2-etap/07-testirovanie/"]::before {
  content: "🧪 ";
}

#quiz-root { margin-top: 1.2rem; }
```

- [ ] **Step 4: Зарегистрировать ассеты в `site/mkdocs.yml`**

Найти:
```yaml
extra_css:
  - site/theme/extra.css

extra_javascript:
  - site/theme/compare-tables.js
```
Заменить на:
```yaml
extra_css:
  - site/theme/extra.css
  - site/theme/quiz.css

extra_javascript:
  - site/theme/compare-tables.js
  # quiz-config.js — строго раньше quiz.js (quiz.js читает window.QUIZ_CONFIG).
  - site/theme/quiz-config.js
  - site/theme/quiz.js
```

- [ ] **Step 5: Добавить раздел меню в `site/mkdocs.yml`**

Найти конец блока `nav:` (после `- Разбор кейсов (FAQ): manual-3-etap/05-faq.md`) и добавить новый top-level пункт **после** всего раздела «3 этап»:
```yaml
  - 🧪 Тестирование по 2 этапу: manual-2-etap/07-testirovanie.md
```
Полный хвост `nav:` после правки:
```yaml
  - 3 этап (заявка 46):
      - Обзор проекта: manual-3-etap/00-overview.md
      - Общие правила: manual-3-etap/06-general-requirements.md
      - Классификатор: manual-3-etap/01-classifier.md
      - Критерии качества: manual-3-etap/04-video-quality.md
      - Банк примеров: manual-3-etap/07-example-library.md
      - Открытые вопросы: manual-3-etap/02-open-questions.md
      - Частые ошибки: manual-3-etap/03-common-mistakes.md
      - Разбор кейсов (FAQ): manual-3-etap/05-faq.md
  # Отдельный акцентный раздел — самопроверка. Держим top-level (не внутри «2 этап»),
  # чтобы во вкладках Material это была своя вкладка. Дублируется в mkdocs-public.yml.
  - 🧪 Тестирование по 2 этапу: manual-2-etap/07-testirovanie.md
```

- [ ] **Step 6: Добавить тот же пункт в `site/mkdocs-public.yml`**

В `site/mkdocs-public.yml` найти конец блока `nav:` (после `- Частые ошибки: manual-2-etap/06-common-mistakes.md`) и добавить:
```yaml
  # Синхронно с mkdocs.yml. nav при INHERIT заменяется целиком, поэтому пункт нужен и здесь.
  - 🧪 Тестирование по 2 этапу: manual-2-etap/07-testirovanie.md
```

- [ ] **Step 7: Собрать оба профиля, проверить страницу и меню**

```bash
cd site
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict -f mkdocs-public.yml
```
Ожидается: обе сборки — exit 0, без новых WARNING.
Проверить наличие файла: `ls ../../avatar-manual-build/build/manual-2-etap/07-testirovanie/index.html` и `../../avatar-manual-build/build-public/manual-2-etap/07-testirovanie/index.html`.
Открыть `build/manual-2-etap/07-testirovanie/index.html` в браузере: виден заголовок, вводный блок, пустой `#quiz-root`, в левом меню/вкладках пункт «🧪 Тестирование по 2 этапу» выделен жирным и акцентным цветом.

- [ ] **Step 8: Commit**

```bash
cd "d:/ПРОЕКТЫ с Ai/Data-Light. Обучение 2 этап"
git add manual-2-etap/07-testirovanie.md site/theme/quiz-config.js site/theme/quiz.css site/mkdocs.yml site/mkdocs-public.yml
git commit -m "Тестирование 2 этапа: страница-заглушка, отдельный акцентный раздел меню, конфиг квиза"
git push
```

---

### Task 2: Каркас хука `build_quiz_bank.py` (вставка пустого банка)

**Files:**
- Create: `site/hooks/build_quiz_bank.py`
- Create: `site/hooks/tests/test_build_quiz_bank.py`
- Modify: `site/mkdocs.yml` (`hooks:`)

**Interfaces:**
- Consumes: `_build_profile.is_pdf_build`.
- Produces:
  - `TARGET_PAGE = "manual-2-etap/07-testirovanie.md"`;
  - `SOURCE_FILES` — кортеж относительных путей `.md` 2 этапа без `00-overview.md`;
  - `on_page_markdown(markdown, page, config, files)` — на целевой странице заменяет `<!-- QUIZ-BANK -->` на `<script id="quiz-bank" type="application/json">{…}</script>`; на PDF-профиле заменяет на заметку; для прочих страниц возвращает markdown без изменений;
  - `build_bank(sources, manual_yaml_text) -> dict` — пока `{"generatedAt": <iso>, "questions": []}` (наполняется в Задачах 3–8);
  - `_inject(markdown, bank_dict) -> str`.

- [ ] **Step 1: Написать падающий тест `site/hooks/tests/test_build_quiz_bank.py`**

```python
import json
import re

from build_quiz_bank import on_page_markdown, build_bank, TARGET_PAGE, SOURCE_FILES


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
    def __init__(self, site_dir, docs_dir):
        super().__init__()
        self.site_dir = FakeSiteDir(site_dir)
        self["docs_dir"] = docs_dir


PAGE_MD = "# Тестирование\n\nвведение\n\n<!-- QUIZ-BANK -->\n"


def _bank_from_html(html):
    m = re.search(
        r'<script id="quiz-bank" type="application/json">(.*?)</script>', html, re.S
    )
    assert m, html
    return json.loads(m.group(1))


def test_injects_empty_bank_on_target_page(tmp_path):
    cfg = FakeConfig(str(tmp_path / "build"), str(tmp_path))
    out = on_page_markdown(PAGE_MD, FakePage(TARGET_PAGE), cfg, None)
    bank = _bank_from_html(out)
    assert bank["questions"] == []
    assert "generatedAt" in bank
    assert "<!-- QUIZ-BANK -->" not in out


def test_noop_on_other_pages(tmp_path):
    cfg = FakeConfig(str(tmp_path / "build"), str(tmp_path))
    md = "# Другая страница\n\n<!-- QUIZ-BANK -->\n"
    out = on_page_markdown(md, FakePage("manual-2-etap/02-segments.md"), cfg, None)
    assert out == md


def test_pdf_profile_replaces_with_note(tmp_path):
    cfg = FakeConfig(str(tmp_path / "build-pdf"), str(tmp_path))
    out = on_page_markdown(PAGE_MD, FakePage(TARGET_PAGE), cfg, None)
    assert "quiz-bank" not in out
    assert "только на сайте" in out.lower()


def test_source_files_exclude_overview():
    assert not any(f.endswith("00-overview.md") for f in SOURCE_FILES)
    assert "manual-2-etap/02-segments.md" in SOURCE_FILES


def test_build_bank_shape():
    bank = build_bank(sources={}, manual_yaml_text="")
    assert bank["questions"] == []
    assert isinstance(bank["generatedAt"], str)
```

- [ ] **Step 2: Прогнать тест — убедиться, что падает**

Run: `cd site/hooks && python -m pytest tests/test_build_quiz_bank.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'build_quiz_bank'`.

- [ ] **Step 3: Написать `site/hooks/build_quiz_bank.py`**

```python
"""Хук: собирает банк вопросов для страницы самопроверки manual-2-etap/07-testirovanie.md.

Читает структурированные места мануала 2 этапа (кроме 00-overview.md), плюс ручной блок
manual-2-etap/_quiz-manual.yml, и вставляет собранный банк в страницу как
<script id="quiz-bank" type="application/json">…</script> на месте маркера <!-- QUIZ-BANK -->.
Ничего не «додумывает»: вопрос попадает в банк, только если правильный ответ явно задан в
самом мануале (жирным значением поля, заголовком-категорией, числом в keyfacts).

На PDF-профиле квиз бессмыслен (нет интерактива) — маркер заменяется короткой заметкой.
"""

import datetime
import hashlib
import json
import re
from pathlib import Path

from _build_profile import is_pdf_build

TARGET_PAGE = "manual-2-etap/07-testirovanie.md"

# Явный список источников — так 00-overview.md гарантированно вне игры, и добавление
# новой страницы мануала не протекает в тест автоматически (это осознанное решение).
SOURCE_FILES = (
    "manual-2-etap/01-general-requirements.md",
    "manual-2-etap/02-segments.md",
    "manual-2-etap/04-classifier.md",
    "manual-2-etap/05-what-to-label.md",
    "manual-2-etap/05b-what-not-to-label.md",
    "manual-2-etap/06-common-mistakes.md",
    "manual-2-etap/11-example-library.md",
)
MANUAL_YAML = "manual-2-etap/_quiz-manual.yml"

_MARKER = "<!-- QUIZ-BANK -->"
_PDF_NOTE = "> Тестирование доступно только на сайте.\n"


def _slug(text):
    """ASCII-безопасный короткий слаг для id (кириллица → транслит не нужен, достаточно
    хэша рядом; здесь просто чистим до [a-z0-9-])."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "q"


def _make_id(category, topic, dedup_key):
    h = hashlib.sha1(dedup_key.encode("utf-8")).hexdigest()[:8]
    return f"{category}-{_slug(topic)}-{h}"


def _read_sources(config):
    docs_dir = Path(config["docs_dir"])
    out = {}
    for rel in SOURCE_FILES:
        p = docs_dir / rel
        out[rel] = p.read_text(encoding="utf-8") if p.exists() else ""
    return out


def _read_manual_yaml(config):
    p = Path(config["docs_dir"]) / MANUAL_YAML
    return p.read_text(encoding="utf-8") if p.exists() else ""


def build_bank(sources, manual_yaml_text):
    """sources: {relpath: markdown_text}. Возвращает {"generatedAt": iso, "questions": [...]}.
    Экстракторы источников A–F подключаются в Задачах 3–8."""
    questions = []
    # --- Задача 3: questions += extract_numbers(...) ; extract_forbidden_tags(...)
    # --- Задача 4: questions += extract_classifier_video(...)
    # --- Задача 5: questions += extract_broken(...)
    # --- Задача 6: questions += extract_examples(...)
    # --- Задача 7: questions += load_manual_questions(manual_yaml_text)
    _dedup_by_id(questions)
    return {
        "generatedAt": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "questions": questions,
    }


def _dedup_by_id(questions):
    seen = set()
    kept = []
    for q in questions:
        if q["id"] in seen:
            continue
        seen.add(q["id"])
        kept.append(q)
    questions[:] = kept


def _inject(markdown, bank_dict):
    payload = json.dumps(bank_dict, ensure_ascii=False)
    # Экранируем '<' — на случай, если в тексте вопроса встретится '</script>'.
    payload = payload.replace("<", "\\u003c")
    script = f'<script id="quiz-bank" type="application/json">{payload}</script>'
    return markdown.replace(_MARKER, script, 1)


def on_page_markdown(markdown, page, config, files):
    src_uri = page.file.src_uri.replace("\\", "/")
    if src_uri != TARGET_PAGE:
        return markdown
    if _MARKER not in markdown:
        return markdown
    if is_pdf_build(config):
        return markdown.replace(_MARKER, _PDF_NOTE, 1)
    bank = build_bank(_read_sources(config), _read_manual_yaml(config))
    return _inject(markdown, bank)
```

- [ ] **Step 4: Прогнать тест — убедиться, что проходит**

Run: `cd site/hooks && python -m pytest tests/test_build_quiz_bank.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Зарегистрировать хук в `site/mkdocs.yml`**

Найти в списке `hooks:`:
```yaml
  - hooks/build_status_badges.py
  - hooks/friendly_md_link_text.py
```
Заменить на:
```yaml
  - hooks/build_status_badges.py
  - hooks/build_quiz_bank.py
  - hooks/friendly_md_link_text.py
```

- [ ] **Step 6: Полный прогон тестов и сборок**

```bash
cd site/hooks && python -m pytest tests/ -q
```
Expected: 145 passed (было 140, +5).
```bash
cd site
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict -f mkdocs-public.yml
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict -f mkdocs-pdf.yml
```
Expected: три exit 0. В `build/manual-2-etap/07-testirovanie/index.html` есть `<script id="quiz-bank" type="application/json">{"generatedAt":…,"questions":[]}</script>`. В `build-pdf/` на этой странице — текст «Тестирование доступно только на сайте», тега `quiz-bank` нет.

- [ ] **Step 7: Commit**

```bash
cd "d:/ПРОЕКТЫ с Ai/Data-Light. Обучение 2 этап"
git add site/hooks/build_quiz_bank.py site/hooks/tests/test_build_quiz_bank.py site/mkdocs.yml
git commit -m "Тестирование 2 этапа: каркас хука build_quiz_bank.py — вставка пустого банка в страницу, no-op на PDF"
git push
```

---

### Task 3: Экстракторы источников D (числа/правила) и E (запрещённое в сегменте)

**Files:**
- Modify: `site/hooks/build_quiz_bank.py`
- Modify: `site/hooks/tests/test_build_quiz_bank.py`

**Interfaces:**
- Produces:
  - `extract_numbers(sources: dict) -> list[dict]` — вопросы категории `DE` по числовым фактам; каждый рецепт проверяет, что ожидаемое число реально присутствует в исходном тексте страницы (если в мануале число изменили — рецепт молча выпадает, и это ловит тест).
  - `extract_forbidden_tags(sources: dict) -> list[dict]` — вопрос(ы) категории `DE` из списка `<span class="kf-tag">…</span>` в `02-segments.md`.
- Consumes: `_make_id`.

- [ ] **Step 1: Добавить падающие тесты в `test_build_quiz_bank.py`**

```python
from build_quiz_bank import extract_numbers, extract_forbidden_tags

SEGMENTS_KEYFACTS = """# Сегменты

<div class="keyfacts">
<div class="kf-stat">
<div class="kf-value">10–300<span>сек</span></div>
<div class="kf-label">длительность одного сегмента</div>
</div>
<div class="kf-stat">
<div class="kf-value">10<span>сегментов</span></div>
<div class="kf-label">максимум на одном видео</div>
</div>
<div class="kf-forbid">
<div class="kf-tags">
<span class="kf-tag">смену кадра</span>
<span class="kf-tag">склейки</span>
<span class="kf-tag">закадровый голос</span>
<span class="kf-tag">молчание &gt;4 сек и на границах</span>
</div>
</div>
</div>
"""

CLASSIFIER_FIELDS = """# Заполнение классификатора

Классификатор в интерфейсе разметки состоит из **13 полей**. Ниже — каждое поле по порядку.
"""


def test_extract_numbers_segment_duration():
    qs = extract_numbers({"manual-2-etap/02-segments.md": SEGMENTS_KEYFACTS})
    dur = [q for q in qs if "длительност" in q["question"].lower()]
    assert dur, qs
    q = dur[0]
    assert q["category"] == "DE"
    assert q["options"][q["answer"]] == q["options"][0]
    assert "300" in q["options"][0]
    assert len(q["options"]) >= 3
    assert q["review"]["url"].startswith("02-segments.md#")


def test_extract_numbers_recipe_drops_when_number_absent():
    # В тексте нет "13 полей" -> рецепт про число полей не выдаёт вопрос
    qs = extract_numbers({"manual-2-etap/04-classifier.md": "# Классификатор\n\nбез числа полей\n"})
    assert not [q for q in qs if "полей" in q["question"].lower()]


def test_extract_numbers_classifier_field_count_present():
    qs = extract_numbers({"manual-2-etap/04-classifier.md": CLASSIFIER_FIELDS})
    fld = [q for q in qs if "полей" in q["question"].lower()]
    assert fld and fld[0]["options"][0] == "13"


def test_extract_forbidden_tags():
    qs = extract_forbidden_tags({"manual-2-etap/02-segments.md": SEGMENTS_KEYFACTS})
    assert qs
    q = qs[0]
    assert q["category"] == "DE"
    assert len(q["options"]) >= 3
    # верный вариант — один из запрещённых тегов
    assert q["options"][0] in {"смену кадра", "склейки", "закадровый голос",
                               "молчание >4 сек и на границах"} or "молчание" in q["options"][0]
    # неверные варианты — «допустимые» вещи, не из списка тегов
    assert "пиксельность на фоне" in q["options"] or "лёгкий фоновый шум" in q["options"]
```

- [ ] **Step 2: Прогнать — убедиться, что падает**

Run: `cd site/hooks && python -m pytest tests/test_build_quiz_bank.py -q`
Expected: FAIL — `ImportError: cannot import name 'extract_numbers'`.

- [ ] **Step 3: Реализовать оба экстрактора в `build_quiz_bank.py`**

Добавить перед `build_bank`:

```python
_KF_TAG_RE = re.compile(r'<span class="kf-tag">(.*?)</span>')


def _canon(text):
    return text.replace("&gt;", ">").replace("&lt;", "<").strip()


# Рецепты источника D. Каждый: страница, регэксп-подтверждение (ожидаемое число должно
# присутствовать в тексте страницы), текст вопроса, верный вариант, набор неверных, якорь.
_NUMBER_RECIPES = [
    {
        "page": "manual-2-etap/02-segments.md",
        "confirm": r"10\s*[–-]\s*300",
        "question": "Какова допустимая длительность одного сегмента?",
        "correct": "от 10 до 300 секунд",
        "wrong": ["от 5 до 60 секунд", "от 10 до 120 секунд", "от 30 до 600 секунд"],
        "anchor": "определение-и-границы",
        "title": "Сегменты",
    },
    {
        "page": "manual-2-etap/02-segments.md",
        "confirm": r"максимум\s+10\s+сегментов|10\s*<span>сегментов",
        "question": "Сколько сегментов максимум можно выделить на одном видео?",
        "correct": "10",
        "wrong": ["5", "8", "без ограничения"],
        "anchor": "определение-и-границы",
        "title": "Сегменты",
    },
    {
        "page": "manual-2-etap/04-classifier.md",
        "confirm": r"\*\*13 полей\*\*|состоит из \*\*13",
        "question": "Из скольких полей состоит классификатор на 2 этапе?",
        "correct": "13",
        "wrong": ["10", "12", "15"],
        "anchor": "поля-классификатора",
        "title": "Классификатор",
    },
    {
        "page": "manual-2-etap/02-segments.md",
        "confirm": r"10:15",
        "question": "Какова максимальная длина исходного видео, которое ещё берём в работу?",
        "correct": "10:15",
        "wrong": ["10:00", "9:30", "15:00"],
        "anchor": "определение-и-границы",
        "title": "Сегменты",
    },
]

# «Допустимые» вещи — пул неверных вариантов для вопроса про запрещённое в сегменте.
_ALLOWED_DISTRACTORS = [
    "пиксельность на фоне",
    "лёгкий фоновый шум",
    "блики на очках",
    "медленный плавный зум",
    "чёрно-белое изображение",
]


def extract_numbers(sources):
    out = []
    for r in _NUMBER_RECIPES:
        text = sources.get(r["page"], "")
        if not text or not re.search(r["confirm"], text):
            continue
        out.append(
            {
                "id": _make_id("DE", r["question"], r["page"] + r["correct"]),
                "category": "DE",
                "topic": r["title"],
                "question": r["question"],
                "options": [r["correct"], *r["wrong"]],
                "answer": 0,
                "review": {"title": r["title"], "url": f'{r["page"].split("/")[-1]}#{r["anchor"]}'},
            }
        )
    return out


def extract_forbidden_tags(sources):
    text = sources.get("manual-2-etap/02-segments.md", "")
    tags = [_canon(t) for t in _KF_TAG_RE.findall(text)]
    if len(tags) < 3:
        return []
    correct = tags[0]  # любой тег из списка; порядок вариантов всё равно перемешает JS
    wrong = _ALLOWED_DISTRACTORS[:3]
    return [
        {
            "id": _make_id("DE", "запрещено в сегменте", "forbidden-tags"),
            "category": "DE",
            "topic": "Сегменты",
            "question": "Что из перечисленного НЕ должно попасть внутрь сегмента?",
            "options": [correct, *wrong],
            "answer": 0,
            "review": {"title": "Сегменты", "url": "02-segments.md#определение-и-границы"},
        }
    ]
```

Подключить в `build_bank` (заменить строку-заглушку `# --- Задача 3: …`):
```python
    questions += extract_numbers(sources)
    questions += extract_forbidden_tags(sources)
```

- [ ] **Step 4: Прогнать тесты**

Run: `cd site/hooks && python -m pytest tests/test_build_quiz_bank.py -q`
Expected: PASS (все, включая 4 новых).

- [ ] **Step 5: Проверить на живом мануале**

Run:
```bash
cd site/hooks && python -c "
from pathlib import Path
import build_quiz_bank as m
root = Path('../../')
src = {r: (root/r).read_text(encoding='utf-8') for r in m.SOURCE_FILES}
for q in m.extract_numbers(src) + m.extract_forbidden_tags(src):
    print(q['id'], '|', q['question'], '->', q['options'][0])
"
```
Expected: печатает 4–5 вопросов; в каждом верный вариант осмысленный, `review.url` указывает на существующий якорь (`02-segments.md#определение-и-границы`, `04-classifier.md#поля-классификатора`).

- [ ] **Step 6: Commit**

```bash
cd "d:/ПРОЕКТЫ с Ai/Data-Light. Обучение 2 этап"
git add site/hooks/build_quiz_bank.py site/hooks/tests/test_build_quiz_bank.py
git commit -m "build_quiz_bank.py: экстракторы источников D (числа/правила по рецептам) и E (запрещённое в сегменте)"
git push
```

---

### Task 4: Экстрактор источника A (поля классификатора по видео)

**Files:**
- Modify: `site/hooks/build_quiz_bank.py`
- Modify: `site/hooks/tests/test_build_quiz_bank.py`

**Interfaces:**
- Produces: `extract_classifier_video(sources: dict) -> list[dict]` — вопросы категории `A`. Разбирает `manual-2-etap/04-classifier.md`: секции `### N. <Поле>`, их `<ul class="value-checklist"><li>значение</li>…`, и строки-примеры `- [**Значение** — примечание (тайм-код)](url)`. Вопрос строится, только если жирный текст в начале подписи **точно совпадает** (после нормализации регистра/пробелов) с одним из значений чек-листа этого поля.
- Consumes: `_make_id`, `_section_utils.extract_section`.

- [ ] **Step 1: Добавить падающие тесты**

```python
from build_quiz_bank import extract_classifier_video

CLASSIFIER_A = """# Заполнение классификатора

## Поля классификатора

### 3. Объём и поза тела человека в кадре

<ul class="value-checklist">
<li>Голова</li>
<li>Голова и плечи</li>
<li>Голова, плечи и руки</li>
<li>Сидя в полный рост</li>
<li>Стоя в полный рост</li>
</ul>

**Примеры:**

- [**Голова и плечи** — кисти рук не видны (78.4–95.9)](https://ex.test/a.mp4)
- [**Голова, плечи и руки** — (18.9–29.3)](https://ex.test/b.mp4)

### 4. Преобладающий ракурс

<ul class="value-checklist">
<li>Анфас</li>
<li>Полуоборот (3/4)</li>
<li>Профиль</li>
</ul>

**Примеры:**

- [**Анфас** (0:06.48–0:18.06)](https://ex.test/c.mp4)
- [**Ракурс меняется в пределах ролика** — берём преобладающее](https://ex.test/d.mp4)
"""


def test_extract_classifier_video_basic():
    qs = extract_classifier_video({"manual-2-etap/04-classifier.md": CLASSIFIER_A})
    poses = [q for q in qs if q["topic"] == "Объём и поза тела человека в кадре"]
    assert len(poses) == 2
    q = poses[0]
    assert q["category"] == "A"
    assert q["videoUrl"] == "https://ex.test/a.mp4"
    assert q["videoKind"] == "mp4"
    assert q["videoStart"] == 78.4
    assert q["options"][0] == "Голова и плечи"
    assert set(q["options"]) <= {
        "Голова", "Голова и плечи", "Голова, плечи и руки",
        "Сидя в полный рост", "Стоя в полный рост",
    }
    assert len(q["options"]) >= 3
    assert q["answer"] == 0
    assert q["review"]["url"] == "04-classifier.md#3-объём-и-поза-тела-человека-в-кадре"


def test_extract_classifier_video_skips_non_matching_caption():
    qs = extract_classifier_video({"manual-2-etap/04-classifier.md": CLASSIFIER_A})
    rakurs = [q for q in qs if q["topic"] == "Преобладающий ракурс"]
    assert len(rakurs) == 1  # "Ракурс меняется…" не совпал со значением чек-листа -> пропущен
    assert rakurs[0]["options"][0] == "Анфас"
    assert rakurs[0]["videoStart"] == 6.48


def test_extract_classifier_video_timecode_mm_ss():
    qs = extract_classifier_video({"manual-2-etap/04-classifier.md": CLASSIFIER_A})
    anfas = [q for q in qs if q["topic"] == "Преобладающий ракурс"][0]
    # 0:06.48 -> 6.48 сек
    assert abs(anfas["videoStart"] - 6.48) < 0.001
```

- [ ] **Step 2: Прогнать — убедиться, что падает**

Run: `cd site/hooks && python -m pytest tests/test_build_quiz_bank.py -q`
Expected: FAIL — `ImportError: cannot import name 'extract_classifier_video'`.

- [ ] **Step 3: Реализовать экстрактор**

В начало файла добавить импорт:
```python
from _section_utils import extract_section
```

Добавить перед `build_bank`:

```python
_FIELD_HEADING_RE = re.compile(r'^### \d+\.\s+(.*?)\s*$', re.M)
_CHECKLIST_RE = re.compile(
    r'<ul class="value-checklist">(.*?)</ul>', re.S
)
_LI_RE = re.compile(r'<li>(.*?)</li>', re.S)
_EXAMPLE_LINE_RE = re.compile(
    r'^\s*[-*]\s+\[\*\*(?P<value>[^*]+?)\*\*(?P<rest>[^\]]*)\]\((?P<url>[^)]+)\)', re.M
)
_TIMECODE_RE = re.compile(
    r'\(?(?P<a>\d+):(?P<b>\d+(?:\.\d+)?)|\(?(?P<sec>\d+(?:\.\d+)?)\s*[–-]'
)


def _norm_value(text):
    return re.sub(r'\s+', ' ', text).strip().lower()


def _parse_timecode(rest):
    """Начало примера в секундах из хвоста подписи. Понимает '(78.4–95.9)' и '(0:06.48–…)'.
    None, если тайм-кода нет."""
    m = re.search(r'\((?:до\s*)?(\d+):(\d+(?:\.\d+)?)', rest)
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    m = re.search(r'\((?:до\s*)?(\d+(?:\.\d+)?)\s*[–-]', rest)
    if m:
        return float(m.group(1))
    m = re.search(r'\((?:до\s*)?(\d+(?:\.\d+)?)\)', rest)
    if m:
        return float(m.group(1))
    return None


def _video_kind(url):
    if "vkvideo.ru" in url or "vk.com/video" in url:
        return "vk"
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return "mp4"


def _split_classifier_fields(text):
    """[(field_name, section_body)] по секциям '### N. <Поле>' внутри '## Поля классификатора'."""
    body = extract_section(text, "Поля классификатора")
    if body is None:
        body = text
    matches = list(_FIELD_HEADING_RE.finditer(body))
    out = []
    for i, mt in enumerate(matches):
        start = mt.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        out.append((mt.group(1).strip(), body[start:end]))
    return out


def _field_anchor(index_word, field_name):
    # slug как у pymdownx.slugs.slugify(case=lower): нижний регистр, пробелы -> '-',
    # пунктуация выкидывается, кириллица сохраняется. Заголовок вида "3. Объём и поза…".
    raw = f"{index_word} {field_name}".lower()
    raw = raw.replace("(", "").replace(")", "").replace(",", "").replace(".", "")
    raw = re.sub(r'\s+', '-', raw.strip())
    return raw


def extract_classifier_video(sources):
    text = sources.get("manual-2-etap/04-classifier.md", "")
    if not text:
        return []
    out = []
    # индекс поля берём из самого заголовка "### N."
    heading_iter = list(re.finditer(r'^### (\d+)\.\s+(.*?)\s*$', text, re.M))
    idx_by_name = {m.group(2).strip(): m.group(1) for m in heading_iter}
    for field_name, section in _split_classifier_fields(text):
        cl = _CHECKLIST_RE.search(section)
        if not cl:
            continue
        values = [re.sub(r'<[^>]+>', '', v).strip() for v in _LI_RE.findall(cl.group(1))]
        values = [v for v in values if v]
        if len(values) < 3:
            continue
        by_norm = {_norm_value(v): v for v in values}
        for ex in _EXAMPLE_LINE_RE.finditer(section):
            value_raw = ex.group("value").strip()
            canon = by_norm.get(_norm_value(value_raw))
            if canon is None:
                continue  # подпись не совпала со значением поля — не берём
            url = ex.group("url").strip()
            rest = ex.group("rest") or ""
            start = _parse_timecode(rest)
            wrong = [v for v in values if v != canon]
            random_wrong = wrong[:3] if len(wrong) >= 3 else wrong
            idx_word = idx_by_name.get(field_name, "")
            q = {
                "id": _make_id("A", field_name, url),
                "category": "A",
                "topic": field_name,
                "question": f"Определите по видео: {field_name.lower()}.",
                "videoUrl": url,
                "videoKind": _video_kind(url),
                "options": [canon, *random_wrong],
                "answer": 0,
                "review": {
                    "title": "Классификатор",
                    "url": f"04-classifier.md#{_field_anchor(idx_word + '.', field_name)}",
                },
            }
            if start is not None:
                q["videoStart"] = round(start, 2)
            out.append(q)
    return out
```

Подключить в `build_bank`:
```python
    questions += extract_classifier_video(sources)
```

- [ ] **Step 4: Прогнать тесты**

Run: `cd site/hooks && python -m pytest tests/test_build_quiz_bank.py -q`
Expected: PASS. Если тест `test_extract_classifier_video_basic` спорит по якорю — сверить slug: заголовок `### 3. Объём и поза тела человека в кадре` → ожидаемый id `3-объём-и-поза-тела-человека-в-кадре`; поправить `_field_anchor` до совпадения.

- [ ] **Step 5: Проверить на живом мануале + сверить якоря сборкой**

```bash
cd site/hooks && python -c "
from pathlib import Path
import build_quiz_bank as m
root = Path('../../')
src = {r: (root/r).read_text(encoding='utf-8') for r in m.SOURCE_FILES}
qs = m.extract_classifier_video(src)
print(len(qs), 'вопросов A')
for q in qs[:12]:
    print(q['topic'], '|', q['options'][0], '| start=', q.get('videoStart'), '|', q['review']['url'])
"
```
Expected: ≥6 вопросов; поля «Объём и поза тела…», «Преобладающий ракурс», «Освещение», «Фон» присутствуют; все `review.url` вида `04-classifier.md#<slug>`.
Затем — сверка якорей с реальной сборкой:
```bash
cd site && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict
grep -o 'id="[^"]*"' ../../avatar-manual-build/build/manual-2-etap/04-classifier/index.html | sort -u
```
Каждый `#<slug>` из `review.url` должен встречаться в этом списке `id=`. Несовпадения — поправить `_field_anchor`.

- [ ] **Step 6: Commit**

```bash
cd "d:/ПРОЕКТЫ с Ai/Data-Light. Обучение 2 этап"
git add site/hooks/build_quiz_bank.py site/hooks/tests/test_build_quiz_bank.py
git commit -m "build_quiz_bank.py: экстрактор источника A — поля классификатора по видео-примерам (точное совпадение подписи со значением поля, тайм-код в videoStart)"
git push
```

---

### Task 5: Экстрактор источника B («Битое» / дефекты)

**Files:**
- Modify: `site/hooks/build_quiz_bank.py`
- Modify: `site/hooks/tests/test_build_quiz_bank.py`

**Interfaces:**
- Produces: `extract_broken(sources: dict) -> list[dict]` — вопросы категории `B` из двух подисточников:
  1. `11-example-library.md`, раздел `## Битое — примеры дефектов` — список `- [подпись](url)`, подпись = описание дефекта. Вопрос «Какой дефект в этом видео?»; неверные — подписи других пунктов этого списка.
  2. `05b-what-not-to-label.md`, подразделы `### <Категория> {: .field-label-heading }` внутри `## 🚫 Полностью исключённые типы видео`, их списки `**Калибровочные примеры…**` — но пункт берётся, только если подпись **не содержит** маркеров отрицания/смягчения (`нет`, `некритичн`, `для сравнения`, `допустим`, `не всегда`, `баг плеера`). Вопрос «Что не так с этим видео (почему в „Битое“)?»; верный — заголовок подраздела; неверные — соседние заголовки.
- Consumes: `_make_id`, `_video_kind`, `extract_section`.

- [ ] **Step 1: Добавить падающие тесты**

```python
from build_quiz_bank import extract_broken

LIB_BROKEN = """# Банк примеров

## Битое — примеры дефектов

- [Смена кадра в конце](https://ex.test/s1.mp4)
- [Кашель перебивает говорящего](https://ex.test/s2.mp4)
- [Звук ветра слишком громкий](https://ex.test/s3.mp4)
- [Наложение полупрозрачного кадра](https://ex.test/s4.mp4)

`[Комментарии к мануалу от заказчика, 06.09.2026]`

## Артефакт

- [Мерцание пиксельное](https://ex.test/art.mp4)
"""

NOT_LABEL_B = """# Что не размечаем / Битое

## 🚫 Полностью исключённые типы видео

<div class="field-label-row" markdown="1">

### Склейки {: .field-label-heading }

Склейка внутри сегмента — брак.

</div>

**Калибровочные примеры:**

- [В начале склейка с наложением](https://ex.test/skl1.mp4).
- [3 склейки подряд](https://ex.test/skl2.mp4).

<div class="field-label-row" markdown="1">

### Пиксельность {: .field-label-heading }

Черты лица смазаны.

</div>

**Калибровочные примеры пиксельности:**

- [Нет пиксельности, для сравнения](https://ex.test/px0.mp4).
- [Некритичная пиксельность (из-за освещения)](https://ex.test/px1.mp4).
- [Пиксельность — пример 2](https://ex.test/px2.mp4).
"""


def test_extract_broken_from_example_library():
    qs = extract_broken({"manual-2-etap/11-example-library.md": LIB_BROKEN})
    lib = [q for q in qs if q["review"]["url"].startswith("11-example-library.md")]
    assert len(lib) == 4
    q = lib[0]
    assert q["category"] == "B"
    assert q["videoUrl"] == "https://ex.test/s1.mp4"
    assert q["options"][0] == "Смена кадра в конце"
    assert len(q["options"]) >= 3
    assert all(opt in {"Смена кадра в конце", "Кашель перебивает говорящего",
                       "Звук ветра слишком громкий", "Наложение полупрозрачного кадра"}
               for opt in q["options"])


def test_extract_broken_from_excluded_types_filters_negations():
    qs = extract_broken({"manual-2-etap/05b-what-not-to-label.md": NOT_LABEL_B})
    b05 = [q for q in qs if q["review"]["url"].startswith("05b-")]
    urls = {q["videoUrl"] for q in b05}
    assert "https://ex.test/skl1.mp4" in urls
    assert "https://ex.test/skl2.mp4" in urls
    assert "https://ex.test/px2.mp4" in urls
    assert "https://ex.test/px0.mp4" not in urls  # "Нет пиксельности, для сравнения"
    assert "https://ex.test/px1.mp4" not in urls  # "Некритичная пиксельность"
    q = [q for q in b05 if q["videoUrl"] == "https://ex.test/skl1.mp4"][0]
    assert q["options"][0] == "Склейки"
    assert "Пиксельность" in q["options"]
    assert len(q["options"]) >= 3
```

- [ ] **Step 2: Прогнать — убедиться, что падает**

Run: `cd site/hooks && python -m pytest tests/test_build_quiz_bank.py -q`
Expected: FAIL — `ImportError: cannot import name 'extract_broken'`.

- [ ] **Step 3: Реализовать экстрактор**

```python
_NEGATION_MARKERS = ("нет ", "некритичн", "для сравнения", "допустим", "не всегда", "баг плеер")
_LINK_ITEM_RE = re.compile(r'^\s*[-*]\s+\[(?P<cap>[^\]]+)\]\((?P<url>[^)]+)\)', re.M)
_EXCLUDED_SUBHEAD_RE = re.compile(
    r'^###\s+(?P<name>.+?)\s+\{:\s*\.field-label-heading\s*\}\s*$', re.M
)


def _clean_caption(cap):
    cap = re.sub(r'\*\*(.+?)\*\*', r'\1', cap)  # снять bold
    return cap.strip().rstrip(".").strip()


def _has_negation(cap):
    low = cap.lower()
    return any(mk in low for mk in _NEGATION_MARKERS)


def _extract_broken_from_library(text):
    body = extract_section(text, "Битое — примеры дефектов")
    if body is None:
        return []
    items = [(_clean_caption(m.group("cap")), m.group("url").strip())
             for m in _LINK_ITEM_RE.finditer(body)]
    items = [(c, u) for c, u in items if c and not _has_negation(c)]
    if len(items) < 3:
        return []
    all_caps = [c for c, _ in items]
    out = []
    for cap, url in items:
        wrong = [c for c in all_caps if c != cap][:3]
        if len(wrong) < 2:
            continue
        out.append({
            "id": _make_id("B", "битое дефект", url),
            "category": "B",
            "topic": "Что не размечаем / Битое",
            "question": "Какой дефект в этом видео (почему оно уходит в «Битое»)?",
            "videoUrl": url,
            "videoKind": _video_kind(url),
            "options": [cap, *wrong],
            "answer": 0,
            "review": {"title": "Банк примеров",
                       "url": "11-example-library.md#битое--примеры-дефектов"},
        })
    return out


def _extract_broken_from_excluded(text):
    body = extract_section(text, "🚫 Полностью исключённые типы видео")
    if body is None:
        return []
    heads = list(_EXCLUDED_SUBHEAD_RE.finditer(body))
    if len(heads) < 3:
        return []
    names = [h.group("name").strip() for h in heads]
    out = []
    for i, h in enumerate(heads):
        name = names[i]
        seg_start = h.end()
        seg_end = heads[i + 1].start() if i + 1 < len(heads) else len(body)
        segment = body[seg_start:seg_end]
        others = [n for n in names if n != name][:3]
        if len(others) < 2:
            continue
        for m in _LINK_ITEM_RE.finditer(segment):
            cap = _clean_caption(m.group("cap"))
            url = m.group("url").strip()
            if not cap or _has_negation(cap):
                continue
            out.append({
                "id": _make_id("B", name, url),
                "category": "B",
                "topic": "Что не размечаем / Битое",
                "question": "Что не так с этим видео — почему его нельзя размечать?",
                "videoUrl": url,
                "videoKind": _video_kind(url),
                "options": [name, *others],
                "answer": 0,
                "review": {"title": "Что не размечаем / Битое",
                           "url": "05b-what-not-to-label.md#-полностью-исключённые-типы-видео"},
            })
    return out


def extract_broken(sources):
    out = []
    out += _extract_broken_from_library(sources.get("manual-2-etap/11-example-library.md", ""))
    out += _extract_broken_from_excluded(sources.get("manual-2-etap/05b-what-not-to-label.md", ""))
    return out
```

Подключить в `build_bank`:
```python
    questions += extract_broken(sources)
```

- [ ] **Step 4: Прогнать тесты**

Run: `cd site/hooks && python -m pytest tests/test_build_quiz_bank.py -q`
Expected: PASS. Если спорит якорь `05b-what-not-to-label.md#-полностью-исключённые-типы-видео` — свериться со сборкой (Step 5) и поправить.

- [ ] **Step 5: Проверить на живом мануале + сверить якоря**

```bash
cd site/hooks && python -c "
from pathlib import Path
import build_quiz_bank as m
root = Path('../../')
src = {r: (root/r).read_text(encoding='utf-8') for r in m.SOURCE_FILES}
qs = m.extract_broken(src)
print(len(qs), 'вопросов B')
for q in qs[:15]:
    print(q['options'][0], '<-', q['videoUrl'].rsplit('/',1)[-1], '|', q['review']['url'])
"
cd ../.. && grep -o 'id="[^"]*"' ../avatar-manual-build/build/manual-2-etap/05b-what-not-to-label/index.html | grep исключ
grep -o 'id="[^"]*"' ../avatar-manual-build/build/manual-2-etap/11-example-library/index.html | grep -i дефект
```
Expected: ≥8 вопросов B; ни одной подписи с «нет/некритичн/для сравнения»; якоря `review.url` совпадают с `id=` в собранных страницах.

- [ ] **Step 6: Commit**

```bash
cd "d:/ПРОЕКТЫ с Ai/Data-Light. Обучение 2 этап"
git add site/hooks/build_quiz_bank.py site/hooks/tests/test_build_quiz_bank.py
git commit -m "build_quiz_bank.py: экстрактор источника B — «Битое»/дефекты (банк примеров + исключённые типы с фильтром контрпримеров)"
git push
```

---

### Task 6: Экстрактор источника C (позитив/антипримеры)

**Files:**
- Modify: `site/hooks/build_quiz_bank.py`
- Modify: `site/hooks/tests/test_build_quiz_bank.py`

**Interfaces:**
- Produces: `extract_examples(sources: dict) -> list[dict]` — вопросы категории `C` из `manual-2-etap/05-what-to-label.md`, раздел `## Примеры (позитивные)`. Блоки `**Пример N:** <url или [текст](url)>` (+ строка картинки-кадра + подпись). Вопрос: «Это видео — подходящий сегмент или «Битое»?»; варианты `["Подходит для разметки", "В «Битое»", "Нужно поделить на 2 сегмента"]`; для `**Пример**` верный — «Подходит для разметки». (Антипримеры на этой странице отсутствуют — их блок переехал в 05b; поэтому источник C даёт только позитив, верный ответ всегда «Подходит». Это осознанно: вопрос проверяет узнавание годного видео.)
- Consumes: `_make_id`, `_video_kind`, `extract_section`.

- [ ] **Step 1: Добавить падающие тесты**

```python
from build_quiz_bank import extract_examples

WHAT_TO_LABEL_C = """# Что размечаем

## Примеры (позитивные)

**Пример 1:** https://vkvideo.ru/video712360465_456239217
![Пример 1: женщина на нейтральном тёмном фоне](assets/example1-frame.jpeg)
Отрывок с речью на нейтральном фоне — лицо чётко видно. **Подходящий сегмент: 0:02 – 02:57.**

**Пример 4:** [Пример 4](assets/Pamela%20Anderson.mp4)
![Пример 4: женщина крупным планом](assets/example4-frame.jpeg)
Яркий фон не мешает — человек чётко виден.

`[Инстр. Kandinsky-Аватар, стр.5-7]`

## Эталонное видео (без замечаний)

[Пример](https://ex.test/etalon.mp4)
"""


def test_extract_examples_positive():
    qs = extract_examples({"manual-2-etap/05-what-to-label.md": WHAT_TO_LABEL_C})
    assert len(qs) == 2
    q = qs[0]
    assert q["category"] == "C"
    assert q["videoUrl"] == "https://vkvideo.ru/video712360465_456239217"
    assert q["videoKind"] == "vk"
    assert q["options"][q["answer"]] == "Подходит для разметки"
    assert q["options"][0] == "Подходит для разметки"
    assert len(q["options"]) == 3
    assert q["review"]["url"] == "05-what-to-label.md#примеры-позитивные"


def test_extract_examples_local_mp4_kind():
    qs = extract_examples({"manual-2-etap/05-what-to-label.md": WHAT_TO_LABEL_C})
    p4 = qs[1]
    assert p4["videoKind"] == "mp4"
    assert p4["videoUrl"].endswith(".mp4")
```

- [ ] **Step 2: Прогнать — убедиться, что падает**

Run: `cd site/hooks && python -m pytest tests/test_build_quiz_bank.py -q`
Expected: FAIL — `ImportError: cannot import name 'extract_examples'`.

- [ ] **Step 3: Реализовать экстрактор**

```python
_EXAMPLE_BLOCK_RE = re.compile(
    r'\*\*Пример (?P<n>\d+):\*\*[ \t]*'
    r'(?:\[(?P<txt>[^\]]*)\]\((?P<lurl>[^)]+)\)|(?P<burl>\S+))',
    re.M,
)
_C_OPTIONS = ["Подходит для разметки", "В «Битое»", "Нужно поделить на 2 сегмента"]


def extract_examples(sources):
    text = sources.get("manual-2-etap/05-what-to-label.md", "")
    if not text:
        return []
    body = extract_section(text, "Примеры (позитивные)")
    if body is None:
        return []
    out = []
    for m in _EXAMPLE_BLOCK_RE.finditer(body):
        url = (m.group("lurl") or m.group("burl") or "").strip()
        if not url or url.startswith("!"):
            continue
        out.append({
            "id": _make_id("C", "подходящий сегмент", url),
            "category": "C",
            "topic": "Что размечаем",
            "question": "Это видео — подходящий сегмент или его нужно отправить в «Битое»?",
            "videoUrl": url,
            "videoKind": _video_kind(url),
            "options": list(_C_OPTIONS),
            "answer": 0,
            "review": {"title": "Что размечаем",
                       "url": "05-what-to-label.md#примеры-позитивные"},
        })
    return out
```

Подключить в `build_bank`:
```python
    questions += extract_examples(sources)
```

- [ ] **Step 4: Прогнать тесты**

Run: `cd site/hooks && python -m pytest tests/test_build_quiz_bank.py -q`
Expected: PASS.

- [ ] **Step 5: Проверить на живом мануале**

```bash
cd site/hooks && python -c "
from pathlib import Path
import build_quiz_bank as m
root = Path('../../')
src = {r: (root/r).read_text(encoding='utf-8') for r in m.SOURCE_FILES}
for q in m.extract_examples(src):
    print(q['videoKind'], q['videoUrl'])
"
```
Expected: 4–5 вопросов, `videoKind` из `{vk, mp4}`, все `videoUrl` — реальные ссылки из «Примеры (позитивные)».

- [ ] **Step 6: Commit**

```bash
cd "d:/ПРОЕКТЫ с Ai/Data-Light. Обучение 2 этап"
git add site/hooks/build_quiz_bank.py site/hooks/tests/test_build_quiz_bank.py
git commit -m "build_quiz_bank.py: экстрактор источника C — позитивные примеры «подходит/битое/поделить»"
git push
```

---

### Task 7: Ручной блок `_quiz-manual.yml` (источник F) + мёрж

**Files:**
- Create: `manual-2-etap/_quiz-manual.yml`
- Modify: `site/hooks/build_quiz_bank.py`
- Modify: `site/hooks/tests/test_build_quiz_bank.py`
- Modify: `site/mkdocs.yml` (`exclude_docs`)
- Modify: `site/mkdocs-public.yml` (`exclude_docs`)
- Modify: `site/requirements.txt`

**Interfaces:**
- Produces: `load_manual_questions(yaml_text: str) -> list[dict]` — парсит YAML-список, приводит к формату банка (`category="F"`, `answer` пересчитан так, что верный вариант встаёт нулевым), валидирует (≥3 варианта, `answer` в диапазоне, есть `id`/`topic`/`question`/`review`). Некорректный элемент — `ValueError` с понятным текстом.
- Consumes: `yaml` (PyYAML).

- [ ] **Step 1: Добавить падающие тесты**

```python
from build_quiz_bank import load_manual_questions

MANUAL_YAML_OK = '''
- id: seg-boundary-speech
  topic: Границы сегмента
  question: С чего должен начинаться и чем заканчиваться сегмент?
  options:
    - Ровно с начала речи человека и до момента, когда он перестаёт говорить
    - С любого удобного места длиной 10 секунд
    - За 3–4 кадра до первого слова
  answer: 0
  review:
    title: Сегменты
    url: 02-segments.md#определение-и-границы

- id: split-short-pause
  topic: Деление сегмента
  question: Нужно ли делить видео на сегменты из-за короткой паузы в речи?
  video: https://ex.test/pause.mp4
  video_start: 4
  options:
    - "Нет — короткая пауза не повод дробить сегмент"
    - "Да — каждая пауза = новый сегмент"
    - "Да, если пауза дольше 1 секунды"
  answer: 0
  review:
    title: Сегменты
    url: 02-segments.md#когда-объединятьделить-сегмент
'''


def test_load_manual_questions_ok():
    qs = load_manual_questions(MANUAL_YAML_OK)
    assert len(qs) == 2
    q = qs[0]
    assert q["id"] == "seg-boundary-speech"
    assert q["category"] == "F"
    assert q["answer"] == 0
    assert q["options"][0].startswith("Ровно с начала речи")
    assert q["review"]["url"] == "02-segments.md#определение-и-границы"
    q2 = qs[1]
    assert q2["videoUrl"] == "https://ex.test/pause.mp4"
    assert q2["videoKind"] == "mp4"
    assert q2["videoStart"] == 4


def test_load_manual_questions_answer_not_zero_gets_reordered():
    y = '''
- id: x
  topic: T
  question: Q?
  options: [неверно1, верно, неверно2]
  answer: 1
  review: {title: Сегменты, url: 02-segments.md#определение-и-границы}
'''
    q = load_manual_questions(y)[0]
    assert q["options"][0] == "верно"
    assert q["answer"] == 0
    assert set(q["options"]) == {"верно", "неверно1", "неверно2"}


def test_load_manual_questions_rejects_two_options():
    y = '''
- id: x
  topic: T
  question: Q?
  options: [a, b]
  answer: 0
  review: {title: T, url: 02-segments.md#определение-и-границы}
'''
    try:
        load_manual_questions(y)
        assert False, "ожидался ValueError"
    except ValueError as e:
        assert "варианта" in str(e) or "options" in str(e)


def test_load_manual_questions_empty():
    assert load_manual_questions("") == []
    assert load_manual_questions("[]") == []
```

- [ ] **Step 2: Прогнать — убедиться, что падает**

Run: `cd site/hooks && python -m pytest tests/test_build_quiz_bank.py -q`
Expected: FAIL — `ImportError: cannot import name 'load_manual_questions'`.

- [ ] **Step 3: Реализовать `load_manual_questions`**

В начало файла:
```python
import yaml
```

Добавить перед `build_bank`:
```python
def load_manual_questions(yaml_text):
    if not yaml_text or not yaml_text.strip():
        return []
    data = yaml.safe_load(yaml_text)
    if data is None:
        return []
    if not isinstance(data, list):
        raise ValueError("_quiz-manual.yml: на верхнем уровне ожидается список вопросов")
    out = []
    for i, item in enumerate(data):
        where = f"_quiz-manual.yml, вопрос #{i + 1}"
        for key in ("id", "topic", "question", "options", "answer", "review"):
            if key not in item:
                raise ValueError(f"{where}: нет обязательного поля '{key}'")
        opts = list(item["options"])
        if len(opts) < 3:
            raise ValueError(f"{where}: нужно минимум 3 варианта, дано {len(opts)}")
        ans = int(item["answer"])
        if not (0 <= ans < len(opts)):
            raise ValueError(f"{where}: answer={ans} вне диапазона вариантов")
        correct = opts[ans]
        reordered = [correct] + [o for j, o in enumerate(opts) if j != ans]
        review = item["review"]
        if "url" not in review or "title" not in review:
            raise ValueError(f"{where}: review должен содержать title и url")
        q = {
            "id": str(item["id"]),
            "category": "F",
            "topic": str(item["topic"]),
            "question": str(item["question"]),
            "options": reordered,
            "answer": 0,
            "review": {"title": str(review["title"]), "url": str(review["url"])},
        }
        if item.get("video"):
            q["videoUrl"] = str(item["video"])
            q["videoKind"] = _video_kind(q["videoUrl"])
        if item.get("video_start") is not None:
            q["videoStart"] = round(float(item["video_start"]), 2)
        out.append(q)
    return out
```

Подключить в `build_bank` (заменить `# --- Задача 7: …`):
```python
    questions += load_manual_questions(manual_yaml_text)
```

- [ ] **Step 4: Прогнать тесты**

Run: `cd site/hooks && python -m pytest tests/test_build_quiz_bank.py -q`
Expected: PASS.

- [ ] **Step 5: Создать `manual-2-etap/_quiz-manual.yml` с полным набором вопросов**

```yaml
# Ручной блок вопросов для страницы самопроверки (источник F в build_quiz_bank.py).
# Правила без машиночитаемой структуры в мануале. Синхронизировать при правках мануала.
# Формат: options — первым удобнее ставить верный и answer: 0, но можно любой (хук
# переставит верный на нулевую позицию). Минимум 3 варианта. video/video_start — необязательны.

- id: seg-boundary-speech
  topic: Границы сегмента
  question: С чего должен начинаться и чем заканчиваться сегмент?
  options:
    - Ровно с начала речи человека и до момента, когда он перестаёт говорить
    - С любого удобного места длиной не менее 10 секунд
    - За 3–4 кадра до первого слова и на 3–4 кадра после последнего
  answer: 0
  review:
    title: Сегменты
    url: 02-segments.md#определение-и-границы

- id: seg-gap-from-cut
  topic: Границы сегмента
  question: Какой запас нужно оставлять от склейки до границы сегмента?
  options:
    - Совсем небольшой — порядка 3–4 кадров, лишь бы склейка физически не попала в сегмент
    - Несколько секунд с запасом
    - Запас не нужен, границу можно ставить ровно по склейке
  answer: 0
  review:
    title: Сегменты
    url: 02-segments.md#определение-и-границы

- id: seg-split-short-pause
  topic: Деление сегмента
  question: Нужно ли дробить видео на сегменты из-за короткой паузы в речи?
  options:
    - Нет — короткая пауза не повод дробить сегмент
    - Да — каждая пауза начинает новый сегмент
    - Да, если пауза дольше одной секунды
  answer: 0
  review:
    title: Сегменты
    url: 02-segments.md#когда-объединятьделить-сегмент

- id: seg-split-similar
  topic: Деление сегмента
  question: На видео несколько однотипных подходящих фрагментов (поза и ракурс не меняются). Сколько сегментов выделять?
  options:
    - Достаточно 1–2, не больше
    - Все до единого, сколько найдётся
    - Ровно один на всё видео
  answer: 0
  review:
    title: Сегменты
    url: 02-segments.md#когда-объединятьделить-сегмент

- id: seg-and-broken-together
  topic: Битое
  question: Можно ли на одном видео одновременно выделить сегмент и поставить галочку «Битое»?
  options:
    - Нет — это взаимоисключающие действия
    - Да, если сомневаешься в качестве
    - Да, всегда, для подстраховки
  answer: 0
  review:
    title: Что не размечаем / Битое
    url: 05b-what-not-to-label.md#когда-видео-помечается-битое

- id: clf-one-person-one-answer
  topic: Классификатор — общие правила
  question: В кадре один человек. Сколько значений отмечать в поле «Возраст»?
  options:
    - Одно — преобладающую возрастную группу
    - Две соседние группы, чтобы точно попасть
    - Столько, сколько кажется подходящим
  answer: 0
  review:
    title: Классификатор
    url: 04-classifier.md#общие-правила

- id: clf-multi-select-condition
  topic: Классификатор — общие правила
  question: Когда в полях классификатора допустим множественный выбор?
  options:
    - Только когда в кадре одновременно двое и более людей
    - Когда трудно выбрать одно значение
    - Всегда, если значения близки
  answer: 0
  review:
    title: Классификатор
    url: 04-classifier.md#общие-правила

- id: clf-background-people
  topic: Классификатор — общие правила
  question: На фоне за спиной спикера видны другие люди. Учитывать ли их в полях о человеке (пол, возраст, эмоции)?
  options:
    - Нет — заполняем только по центральному говорящему человеку
    - Да — отмечаем характеристики всех, кто попал в кадр
    - Да, если их видно чётко
  answer: 0
  review:
    title: Классификатор
    url: 04-classifier.md#общие-правила

- id: clf-emotion-by-voice
  topic: Эмоции и выражение лица
  question: Человек улыбается, но говорит подавленным, грустным тоном. Какую эмоцию ставить?
  options:
    - По тону голоса — серьёзную/грустную
    - По лицу — положительную
    - Нейтральную, раз признаки противоречат
  answer: 0
  review:
    title: Классификатор
    url: 04-classifier.md#7-эмоции-и-выражение-лица

- id: clf-dialog-vs-monologue
  topic: Тип речи
  question: В кадре двое, но говорит по сути один, а второй лишь коротко поддакивает («ага», кивки со звуком). Это диалог или монолог?
  options:
    - Диалог — второй человек произносит реплики вслух
    - Монолог — говорит в основном один
    - Монолог, потому что второй не задаёт вопросов
  answer: 0
  review:
    title: Классификатор
    url: 04-classifier.md#8-тип-речи
- id: clf-language-dominant
  topic: Язык и акценты
  question: В сегменте человек говорит на 95% по-английски и роняет одно слово по-русски. Какой язык отмечать?
  options:
    - Только английский — преобладающий язык
    - Оба языка
    - Только русский, раз он прозвучал
  answer: 0
  review:
    title: Классификатор
    url: 04-classifier.md#10-язык-и-акценты

- id: clf-people-count-camera
  topic: Количество людей в кадре
  question: Мимо спикера в глубине кадра прошли случайные прохожие. Как это влияет на поле «Количество людей в кадре»?
  options:
    - Никак — считаем только тех, кого снимает камера (спикера и тех, кто рядом с ним в кадре)
    - Каждого прохожего нужно посчитать
    - Ставим «два и более», раз в кадре мелькали люди
  answer: 0
  review:
    title: Классификатор
    url: 04-classifier.md#12-количество-людей-одновременно-находящихся-в-кадре

- id: clf-hands-visible
  topic: Объём и поза тела человека в кадре
  question: В кадре видны кисти рук человека, сидящего за столом. Что ставить в поле «Объём и поза тела»?
  options:
    - Голова, плечи и руки
    - Голова и плечи
    - Сидя в полный рост
  answer: 0
  review:
    title: Классификатор
    url: 04-classifier.md#3-объём-и-поза-тела-человека-в-кадре

- id: zoom-sharp-vs-smooth
  topic: Что не размечаем / Битое
  question: В подходящем фрагменте есть зум камеры. Когда фрагмент всё ещё годится для сегмента?
  options:
    - Если зум медленный и плавный
    - Если зум резкий и быстрый
    - Любой зум делает фрагмент негодным
  answer: 0
  review:
    title: Что не размечаем / Битое
    url: 05b-what-not-to-label.md#-полностью-исключённые-типы-видео

- id: silence-in-segment
  topic: Что не размечаем / Битое
  question: Как поступать с молчанием в начале и в конце сегмента?
  options:
    - Молчания на границах быть не должно — сегмент начинается и кончается речью
    - Пара секунд молчания на входе и выходе допустима
    - Молчание допустимо, если длится меньше 4 секунд
  answer: 0
  review:
    title: Что не размечаем / Битое
    url: 05b-what-not-to-label.md#молчание

- id: label-shorts-format
  topic: Что размечаем
  question: Ролик снят в вертикальном формате shorts. Это само по себе повод для «Битого»?
  options:
    - Нет — формат сам по себе не брак, смотрим на качество и наличие подходящего сегмента
    - Да — вертикальные видео не размечаем
    - Да, если это shorts из соцсети
  answer: 0
  review:
    title: Что размечаем
    url: 05-what-to-label.md#размечаем-выделяем-сегмент-если

- id: face-lost-turn
  topic: Что размечаем
  question: Человек в коротком (~10 сек) фрагменте несколько раз отворачивается так, что лицо полностью пропадает. Годится ли фрагмент?
  options:
    - Нет — в коротком сегменте частая потеря лица недопустима
    - Да — повороты головы не мешают
    - Да, если между поворотами видно анфас
  answer: 0
  review:
    title: Что размечаем
    url: 05-what-to-label.md#размечаем-выделяем-сегмент-если

- id: profile-vs-face-loss
  topic: Преобладающий ракурс
  question: Чем профиль отличается от «потери лица»?
  options:
    - При профиле нос всё ещё виден сбоку; при потере лица нос уходит за угол и не виден
    - Это одно и то же
    - Профиль — это когда виден только затылок
  answer: 0
  review:
    title: Классификатор
    url: 04-classifier.md#4-преобладающий-ракурс
```

- [ ] **Step 6: Добавить `_quiz-manual.yml` в `exclude_docs` обоих конфигов**

В `site/mkdocs.yml` найти в `exclude_docs`:
```
  manual-2-etap/_sources-log.md
```
Добавить следом строку:
```
  manual-2-etap/_quiz-manual.yml
```
То же самое в `site/mkdocs-public.yml` (там список `exclude_docs` полный — добавить ту же строку рядом с `manual-2-etap/_sources-log.md`).

- [ ] **Step 7: Явно зафиксировать PyYAML в `site/requirements.txt`**

Добавить в конец файла:
```
# PyYAML уже тянется транзитивно через mkdocs, но hooks/build_quiz_bank.py импортирует yaml
# напрямую (чтение manual-2-etap/_quiz-manual.yml) — фиксируем явно, как сделано для
# pymdown-extensions выше.
pyyaml>=6
```

- [ ] **Step 8: Прогон тестов и сборок**

```bash
cd site/hooks && python -m pytest tests/ -q
```
Expected: рост числа тестов, всё зелёное.
```bash
cd site
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict -f mkdocs-public.yml
```
Expected: exit 0; в `build/` и `build-public/` **нет** файла `manual-2-etap/_quiz-manual.yml`; на странице теста в `<script id="quiz-bank">` теперь есть вопросы категории `F` (быстрый глазомер: `grep -o '"category":"F"' build/manual-2-etap/07-testirovanie/index.html | wc -l` → 18).

- [ ] **Step 9: Commit**

```bash
cd "d:/ПРОЕКТЫ с Ai/Data-Light. Обучение 2 этап"
git add manual-2-etap/_quiz-manual.yml site/hooks/build_quiz_bank.py site/hooks/tests/test_build_quiz_bank.py site/mkdocs.yml site/mkdocs-public.yml site/requirements.txt
git commit -m "Тестирование 2 этапа: ручной блок _quiz-manual.yml (18 вопросов) + загрузчик load_manual_questions, PyYAML зафиксирован явно"
git push
```

---

### Task 8: Сборка банка целиком + интеграционный тест на живом мануале

**Files:**
- Modify: `site/hooks/build_quiz_bank.py`
- Modify: `site/hooks/tests/test_build_quiz_bank.py`

**Interfaces:**
- Produces: рабочий `build_bank` со всеми источниками; `on_page_markdown` на реальной сборке даёт непустой валидный банк. Плюс функция `_iter_review_targets(bank)` не нужна — проверки в тесте.
- Consumes: `pymdownx.slugs.slugify` (для сверки якорей в тесте).

- [ ] **Step 1: Добавить интеграционные тесты (работают с реальными файлами репозитория)**

```python
import pathlib
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


def _real_sources():
    from build_quiz_bank import SOURCE_FILES
    return {r: (REPO_ROOT / r).read_text(encoding="utf-8") for r in SOURCE_FILES}


def _real_manual_yaml():
    p = REPO_ROOT / "manual-2-etap" / "_quiz-manual.yml"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def test_real_bank_is_reasonably_large():
    bank = build_bank(_real_sources(), _real_manual_yaml())
    qs = bank["questions"]
    assert len(qs) >= 45, f"в банке всего {len(qs)} вопросов"
    by_cat = {}
    for q in qs:
        by_cat.setdefault(q["category"], 0)
        by_cat[q["category"]] += 1
    # каждой категории хватает на её минимум в наборе
    assert by_cat.get("A", 0) >= 3
    assert by_cat.get("B", 0) >= 2
    assert by_cat.get("C", 0) >= 1
    assert by_cat.get("DE", 0) >= 1
    assert by_cat.get("F", 0) >= 2


def test_real_bank_no_duplicate_ids():
    bank = build_bank(_real_sources(), _real_manual_yaml())
    ids = [q["id"] for q in bank["questions"]]
    assert len(ids) == len(set(ids))


def test_real_bank_every_question_wellformed():
    bank = build_bank(_real_sources(), _real_manual_yaml())
    for q in bank["questions"]:
        assert q["options"], q
        assert len(q["options"]) >= 3, q
        assert q["answer"] == 0
        assert q["question"].strip()
        assert q["topic"].strip()
        assert q["review"]["url"]
        if "videoUrl" in q:
            assert q["videoKind"] in {"mp4", "vk", "youtube"}


def test_real_bank_review_anchors_exist():
    from pymdownx.slugs import slugify
    slug = slugify(case="lower")
    heading_re = re.compile(r'^(#{1,6})\s+(.*?)\s*(?:\{:[^}]*\})?\s*$', re.M)

    bank = build_bank(_real_sources(), _real_manual_yaml())
    cache = {}
    for q in bank["questions"]:
        ref = q["review"]["url"]
        assert "#" in ref, ref
        fname, anchor = ref.split("#", 1)
        path = REPO_ROOT / "manual-2-etap" / fname
        assert path.exists(), f"{ref}: файла нет"
        if fname not in cache:
            text = path.read_text(encoding="utf-8")
            slugs = set()
            used = {}
            for m in heading_re.finditer(text):
                base = slug(re.sub(r'<[^>]+>', '', m.group(2)), "-")
                n = used.get(base, 0)
                used[base] = n + 1
                slugs.add(base if n == 0 else f"{base}_{n}")
            cache[fname] = slugs
        assert anchor in cache[fname], f"{ref}: якоря '{anchor}' нет среди {sorted(cache[fname])[:20]}"
```

- [ ] **Step 2: Прогнать — часть тестов, скорее всего, падает по якорям**

Run: `cd site/hooks && python -m pytest tests/test_build_quiz_bank.py -q -k real`
Expected: `test_real_bank_review_anchors_exist` может упасть — если так, посмотреть в сообщении, какой якорь не совпал, и поправить константы `anchor` в `_NUMBER_RECIPES` / `_field_anchor` / `review.url` соответствующего экстрактора, пока тест не станет зелёным. Остальные `real`-тесты должны пройти сразу.

- [ ] **Step 3: Поправить якоря до зелёного**

Обновить строковые якоря в экстракторах (Задачи 3–6) и, при необходимости, в `_quiz-manual.yml`, чтобы каждый `review.url` указывал на реально существующий slug заголовка. Повторять `pytest -k real`, пока не `PASS`.

- [ ] **Step 4: Полный прогон и сборки**

```bash
cd site/hooks && python -m pytest tests/ -q
```
Expected: всё зелёное; записать итоговое число в отчёт задачи (ориентир ~165–175 passed).
```bash
cd site
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict -f mkdocs-public.yml
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict -f mkdocs-pdf.yml
```
Expected: три exit 0, без новых WARNING.

- [ ] **Step 5: Глазами посмотреть на банк**

```bash
cd site/hooks && python -c "
import json, pathlib, build_quiz_bank as m
root = pathlib.Path('../../')
src = {r:(root/r).read_text(encoding='utf-8') for r in m.SOURCE_FILES}
y = (root/'manual-2-etap/_quiz-manual.yml').read_text(encoding='utf-8')
bank = m.build_bank(src, y)
print('всего:', len(bank['questions']))
from collections import Counter
print(Counter(q['category'] for q in bank['questions']))
print(Counter(q['topic'] for q in bank['questions']))
" | cat
```
Expected: ≥45 вопросов, распределение по категориям близко к A≥8, B≥8, C≥4, DE≥4, F=18. Если A/B/C заметно меньше — вернуться к соответствующему экстрактору (в рамках отдельного обсуждения с пользователем, не в этой задаче).

- [ ] **Step 6: Commit**

```bash
cd "d:/ПРОЕКТЫ с Ai/Data-Light. Обучение 2 этап"
git add site/hooks/build_quiz_bank.py site/hooks/tests/test_build_quiz_bank.py manual-2-etap/_quiz-manual.yml
git commit -m "build_quiz_bank.py: сборка банка со всеми источниками + интеграционные тесты на живом мануале (размер, дубли id, существование якорей review)"
git push
```

---

### Task 9: `quiz.js` — стартовый экран, гейт по ФИО, сборка набора из 15

**Files:**
- Create: `site/theme/quiz.js`
- Modify: `site/theme/quiz.css`

**Interfaces:**
- Consumes: `window.QUIZ_CONFIG`; `<script id="quiz-bank" type="application/json">`; контейнер `#quiz-root`.
- Produces (внутренние, используются Задачами 10–12):
  - `QuizState` — объект `{ surname, name, set: Question[], idx, answers: Answer[], startedAt }`.
  - `assembleSet(bank, excludeIds) -> Question[]` — 15 вопросов по таблице категорий с потолком на topic и исключением id прошлой попытки.
  - `shuffle(arr)`, `pickN(arr, n)`.
  - `renderStart()`, `renderQuestion()` (в этой задаче — заглушка-каркас), `mount()`.
  - `LS_KEY = "avatar-quiz:last-ids"`.

- [ ] **Step 1: Создать `site/theme/quiz.js`**

```javascript
/* Самопроверка по 2 этапу. Ванильный JS, активируется только на странице с #quiz-root.
   Данные вопросов — в <script id="quiz-bank">, конфиг — window.QUIZ_CONFIG. */
(function () {
  "use strict";

  var root = document.getElementById("quiz-root");
  if (!root) return;

  var CFG = window.QUIZ_CONFIG || { endpoint: "", token: "", passPercent: 80 };
  var LS_KEY = "avatar-quiz:last-ids";
  var QUESTION_SECONDS = 60;
  var TOTAL = 15;
  var TOPIC_CAP = 6;

  var PLAN = [
    { cat: "A", target: 5, min: 3 },
    { cat: "B", target: 3, min: 2 },
    { cat: "C", target: 2, min: 1 },
    { cat: "DE", target: 2, min: 1 },
    { cat: "F", target: 3, min: 2 }
  ];

  var bank = readBank();
  var state = null;

  function readBank() {
    var el = document.getElementById("quiz-bank");
    if (!el) return { questions: [] };
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return { questions: [] };
    }
  }

  function shuffle(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i];
      a[i] = a[j];
      a[j] = t;
    }
    return a;
  }

  function pickN(arr, n) {
    return shuffle(arr).slice(0, n);
  }

  function readExcludeIds() {
    try {
      var v = JSON.parse(localStorage.getItem(LS_KEY) || "[]");
      return Array.isArray(v) ? v : [];
    } catch (e) {
      return [];
    }
  }

  function assembleSet(allQuestions, excludeIds) {
    var exclude = {};
    excludeIds.forEach(function (id) { exclude[id] = true; });

    var byCat = {};
    allQuestions.forEach(function (q) {
      (byCat[q.category] = byCat[q.category] || []).push(q);
    });

    var chosen = [];
    var topicCount = {};

    function canAdd(q) {
      if (chosen.indexOf(q) !== -1) return false;
      var tc = topicCount[q.topic] || 0;
      return tc < TOPIC_CAP;
    }
    function add(q) {
      chosen.push(q);
      topicCount[q.topic] = (topicCount[q.topic] || 0) + 1;
    }

    // 1-й проход: по плану, сначала без исключённых id
    PLAN.forEach(function (row) {
      var pool = (byCat[row.cat] || []);
      var fresh = shuffle(pool.filter(function (q) { return !exclude[q.id] && canAdd(q); }));
      var stale = shuffle(pool.filter(function (q) { return exclude[q.id] && canAdd(q); }));
      var ordered = fresh.concat(stale);
      var take = Math.min(row.target, ordered.length);
      for (var i = 0; i < take; i++) add(ordered[i]);
    });

    // 2-й проход: добор до TOTAL из всего пула (свежие раньше исключённых)
    if (chosen.length < TOTAL) {
      var restFresh = shuffle(allQuestions.filter(function (q) { return !exclude[q.id] && canAdd(q); }));
      var restStale = shuffle(allQuestions.filter(function (q) { return exclude[q.id] && canAdd(q); }));
      var rest = restFresh.concat(restStale);
      for (var k = 0; k < rest.length && chosen.length < TOTAL; k++) {
        if (canAdd(rest[k])) add(rest[k]);
      }
    }

    // если и теперь мало (крошечный банк) — снимаем потолок по topic
    if (chosen.length < TOTAL) {
      var any = shuffle(allQuestions.filter(function (q) { return chosen.indexOf(q) === -1; }));
      for (var z = 0; z < any.length && chosen.length < TOTAL; z++) chosen.push(any[z]);
    }

    return shuffle(chosen).slice(0, TOTAL);
  }

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    attrs = attrs || {};
    Object.keys(attrs).forEach(function (k) {
      if (k === "class") node.className = attrs[k];
      else if (k === "text") node.textContent = attrs[k];
      else if (k === "html") node.innerHTML = attrs[k];
      else node.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) {
      node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return node;
  }

  function renderStart() {
    root.innerHTML = "";
    var wrap = el("div", { class: "quiz-card quiz-start" });

    if (!bank.questions || bank.questions.length < TOTAL) {
      wrap.appendChild(el("p", {
        class: "quiz-warn",
        text: "Банк вопросов сейчас недоступен или слишком мал. Обновите страницу позже."
      }));
      root.appendChild(wrap);
      return;
    }

    wrap.appendChild(el("h2", { text: "Начать тестирование" }));
    wrap.appendChild(el("p", {
      text: "Введите фамилию и имя — результат будет сохранён. 15 вопросов, по 60 секунд на каждый."
    }));

    var form = el("form", { class: "quiz-fio" });
    var iSurname = el("input", { type: "text", name: "surname", placeholder: "Фамилия", autocomplete: "family-name" });
    var iName = el("input", { type: "text", name: "name", placeholder: "Имя", autocomplete: "given-name" });
    var btn = el("button", { type: "submit", class: "quiz-btn", disabled: "disabled", text: "Начать тест" });

    function sync() {
      var ok = iSurname.value.trim() && iName.value.trim();
      if (ok) btn.removeAttribute("disabled");
      else btn.setAttribute("disabled", "disabled");
    }
    iSurname.addEventListener("input", sync);
    iName.addEventListener("input", sync);

    form.appendChild(iSurname);
    form.appendChild(iName);
    form.appendChild(btn);
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (!iSurname.value.trim() || !iName.value.trim()) return;
      startQuiz(iSurname.value.trim(), iName.value.trim());
    });

    wrap.appendChild(form);
    root.appendChild(wrap);
  }

  function startQuiz(surname, name) {
    var set = assembleSet(bank.questions, readExcludeIds());
    state = {
      surname: surname,
      name: name,
      set: set,
      idx: 0,
      answers: [],
      startedAt: Date.now()
    };
    renderQuestion();
  }

  // Заглушка — полноценно реализуется в Задаче 10.
  function renderQuestion() {
    root.innerHTML = "";
    var q = state.set[state.idx];
    var card = el("div", { class: "quiz-card" });
    card.appendChild(el("div", { class: "quiz-progress", text: "Вопрос " + (state.idx + 1) + " / " + TOTAL }));
    card.appendChild(el("p", { class: "quiz-question", text: q.question }));
    card.appendChild(el("pre", { text: JSON.stringify(q.options, null, 2) }));
    root.appendChild(card);
  }

  function renderResults() {} // Задача 11
  function submitResults() {}  // Задача 12

  // экспорт для отладки из консоли
  window.__quiz = { assembleSet: assembleSet, readBank: readBank, get state() { return state; } };

  renderStart();
})();
```

- [ ] **Step 2: Добавить базовые стили в `site/theme/quiz.css`**

Дописать в конец файла:
```css
.quiz-card {
  border: 1px solid var(--md-default-fg-color--lightest, #e0e0e0);
  border-radius: 10px;
  padding: 1.2rem 1.4rem;
  background: var(--md-default-bg-color, #fff);
  max-width: 720px;
}
.quiz-start h2 { margin-top: 0; }
.quiz-fio { display: flex; flex-wrap: wrap; gap: 0.6rem; margin-top: 0.8rem; }
.quiz-fio input {
  flex: 1 1 200px;
  padding: 0.55rem 0.7rem;
  font-size: 0.95rem;
  border: 1px solid var(--md-default-fg-color--light, #bdbdbd);
  border-radius: 6px;
}
.quiz-btn {
  padding: 0.55rem 1.2rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: #fff;
  background: var(--md-accent-fg-color, #ff6f00);
  border: 0;
  border-radius: 6px;
  cursor: pointer;
}
.quiz-btn[disabled] { opacity: 0.5; cursor: not-allowed; }
.quiz-progress { font-size: 0.85rem; color: var(--md-default-fg-color--light, #757575); }
.quiz-question { font-size: 1.05rem; font-weight: 600; margin: 0.6rem 0 1rem; }
.quiz-warn { color: #c62828; font-weight: 600; }
```

- [ ] **Step 3: Собрать и проверить в браузере**

```bash
cd site && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict
```
Открыть `../../avatar-manual-build/build/manual-2-etap/07-testirovanie/index.html`:
- виден стартовый экран с полями «Фамилия»/«Имя», кнопка «Начать тест» неактивна;
- ввод обоих полей активирует кнопку; клик — показывает «Вопрос 1 / 15», текст вопроса и список вариантов (JSON-заглушка);
- в консоли: `__quiz.assembleSet(__quiz.readBank().questions, []).length` → `15`;
- дважды подряд: `var a = __quiz.assembleSet(b,[]).map(q=>q.id); var c = __quiz.assembleSet(b,a).map(q=>q.id); a.filter(x=>c.includes(x)).length` → заметно меньше 15 (пересечение мало́).

- [ ] **Step 4: Commit**

```bash
cd "d:/ПРОЕКТЫ с Ai/Data-Light. Обучение 2 этап"
git add site/theme/quiz.js site/theme/quiz.css
git commit -m "quiz.js: стартовый экран с гейтом по ФИО и сборка набора из 15 вопросов (план по категориям, потолок на тему, исключение прошлой попытки)"
git push
```

---

### Task 10: `quiz.js` — экран вопроса: видео, таймер 60 с, разбор, «Далее»

**Files:**
- Modify: `site/theme/quiz.js`
- Modify: `site/theme/quiz.css`

**Interfaces:**
- Consumes: `QuizState`, `el()`, `shuffle()`, `renderResults` (Задача 11).
- Produces:
  - `renderQuestion()` — полноценная реализация (замена заглушки из Задачи 9).
  - `buildMedia(q, onReady)` — возвращает DOM-узел плеера; вызывает `onReady()`, когда для `<video>` сработал `loadeddata`/`error` (или сработал предохранитель 8 с), для vk/youtube — через 4 с.
  - `Timer(seconds, onTick, onExpire)` с методами `start()`, `stop()`.
  - `Answer` = `{ id, question, topic, chosen: string|null, correct: string, ok: boolean, review }` — пишется в `state.answers`.

- [ ] **Step 1: Заменить заглушку `renderQuestion` и добавить хелперы плеера/таймера**

В `quiz.js` заменить функцию-заглушку `renderQuestion` и `renderResults`-заглушку соседство не трогаем. Вставить перед `renderQuestion`:

```javascript
  function ytId(url) {
    var m = url.match(/(?:youtube\.com\/(?:shorts\/|watch\?v=)|youtu\.be\/)([A-Za-z0-9_-]+)/);
    return m ? m[1] : "";
  }
  function vkIds(url) {
    var m = url.match(/video(-?\d+)_(\d+)/);
    return m ? { oid: m[1], id: m[2] } : null;
  }

  function buildMedia(q, onReady) {
    if (!q.videoUrl) {
      setTimeout(onReady, 0);
      return null;
    }
    var box = el("div", { class: "quiz-media" });
    if (q.videoKind === "mp4") {
      var v = el("video", {
        src: q.videoUrl + (q.videoStart ? "#t=" + q.videoStart : ""),
        controls: "controls",
        muted: "muted",
        loop: "loop",
        playsinline: "playsinline",
        preload: "auto"
      });
      v.muted = true;
      var fired = false;
      var ready = function () { if (!fired) { fired = true; onReady(); } };
      v.addEventListener("loadeddata", ready);
      v.addEventListener("error", ready);
      setTimeout(ready, 8000);
      v.addEventListener("canplay", function () { v.play().catch(function () {}); });
      box.appendChild(v);
    } else {
      var src = "";
      if (q.videoKind === "youtube") {
        src = "https://www.youtube-nocookie.com/embed/" + ytId(q.videoUrl);
      } else {
        var ids = vkIds(q.videoUrl);
        src = ids ? "https://vk.com/video_ext.php?oid=" + ids.oid + "&id=" + ids.id + "&hd=2" : q.videoUrl;
      }
      box.appendChild(el("iframe", {
        class: "quiz-embed",
        src: src,
        loading: "eager",
        allow: "autoplay; encrypted-media; picture-in-picture",
        allowfullscreen: "allowfullscreen"
      }));
      setTimeout(onReady, 4000);
    }
    return box;
  }

  function Timer(seconds, onTick, onExpire) {
    var total = seconds * 1000;
    var end = 0;
    var raf = 0;
    var stopped = false;
    function frame() {
      if (stopped) return;
      var left = Math.max(0, end - Date.now());
      onTick(left / 1000, left / total);
      if (left <= 0) { stopped = true; onExpire(); return; }
      raf = requestAnimationFrame(frame);
    }
    return {
      start: function () { end = Date.now() + total; stopped = false; raf = requestAnimationFrame(frame); },
      stop: function () { stopped = true; if (raf) cancelAnimationFrame(raf); }
    };
  }

  function timerRing() {
    var NS = "http://www.w3.org/2000/svg";
    var svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", "0 0 40 40");
    svg.setAttribute("class", "quiz-ring");
    var bg = document.createElementNS(NS, "circle");
    bg.setAttribute("cx", "20"); bg.setAttribute("cy", "20"); bg.setAttribute("r", "18");
    bg.setAttribute("class", "quiz-ring-bg");
    var fg = document.createElementNS(NS, "circle");
    fg.setAttribute("cx", "20"); fg.setAttribute("cy", "20"); fg.setAttribute("r", "18");
    fg.setAttribute("class", "quiz-ring-fg");
    var C = 2 * Math.PI * 18;
    fg.setAttribute("stroke-dasharray", String(C));
    fg.setAttribute("stroke-dashoffset", "0");
    var label = document.createElementNS(NS, "text");
    label.setAttribute("x", "20"); label.setAttribute("y", "24");
    label.setAttribute("text-anchor", "middle"); label.setAttribute("class", "quiz-ring-text");
    label.textContent = "60";
    svg.appendChild(bg); svg.appendChild(fg); svg.appendChild(label);
    return {
      node: svg,
      update: function (secLeft, frac) {
        fg.setAttribute("stroke-dashoffset", String(C * (1 - frac)));
        label.textContent = String(Math.ceil(secLeft));
        if (secLeft <= 10) svg.classList.add("warn");
        else svg.classList.remove("warn");
      }
    };
  }
```

Затем заменить тело `renderQuestion`:

```javascript
  function renderQuestion() {
    root.innerHTML = "";
    var q = state.set[state.idx];
    var options = shuffle(q.options.map(function (text, i) {
      return { text: text, correct: i === q.answer };
    }));

    var card = el("div", { class: "quiz-card quiz-qcard" });

    var head = el("div", { class: "quiz-qhead" });
    head.appendChild(el("div", { class: "quiz-progress", text: "Вопрос " + (state.idx + 1) + " / " + TOTAL }));
    var ring = timerRing();
    head.appendChild(ring.node);
    card.appendChild(head);

    card.appendChild(el("p", { class: "quiz-question", text: q.question }));

    var locked = false;
    var timer = Timer(QUESTION_SECONDS, function (secLeft, frac) {
      ring.update(secLeft, frac);
    }, function () {
      if (!locked) lockAnswer(null);
    });

    var media = buildMedia(q, function () {
      if (!locked) timer.start();
    });
    if (media) card.appendChild(media);

    var list = el("div", { class: "quiz-options" });
    var btns = [];
    options.forEach(function (opt) {
      var b = el("button", { type: "button", class: "quiz-option", text: opt.text });
      b.addEventListener("click", function () { if (!locked) lockAnswer(opt.text); });
      btns.push({ b: b, opt: opt });
      list.appendChild(b);
    });
    card.appendChild(list);

    var feedback = el("div", { class: "quiz-feedback", hidden: "hidden" });
    card.appendChild(feedback);

    var next = el("button", { type: "button", class: "quiz-btn quiz-next", hidden: "hidden",
      text: state.idx + 1 < TOTAL ? "Далее" : "Показать результат" });
    next.addEventListener("click", function () {
      state.idx += 1;
      if (state.idx < TOTAL) renderQuestion();
      else renderResults();
    });
    card.appendChild(next);

    root.appendChild(card);

    function lockAnswer(chosenText) {
      locked = true;
      timer.stop();
      var correctText = q.options[q.answer];
      var ok = chosenText === correctText;

      btns.forEach(function (x) {
        x.b.setAttribute("disabled", "disabled");
        if (x.opt.correct) x.b.classList.add("is-correct");
        if (x.opt.text === chosenText && !x.opt.correct) x.b.classList.add("is-wrong");
      });

      feedback.hidden = false;
      if (chosenText === null) {
        feedback.className = "quiz-feedback bad";
        feedback.textContent = "Время вышло. Правильный ответ отмечен зелёным.";
      } else if (ok) {
        feedback.className = "quiz-feedback good";
        feedback.textContent = "Верно!";
      } else {
        feedback.className = "quiz-feedback bad";
        feedback.textContent = "Неверно. Правильный ответ отмечен зелёным.";
      }

      state.answers.push({
        id: q.id,
        question: q.question,
        topic: q.topic,
        chosen: chosenText,
        correct: correctText,
        ok: ok,
        review: q.review
      });

      next.hidden = false;
      next.focus();
    }
  }
```

- [ ] **Step 2: Добавить стили экрана вопроса в `site/theme/quiz.css`**

```css
.quiz-qhead { display: flex; align-items: center; justify-content: space-between; }
.quiz-ring { width: 44px; height: 44px; }
.quiz-ring-bg { fill: none; stroke: var(--md-default-fg-color--lightest, #e0e0e0); stroke-width: 4; }
.quiz-ring-fg {
  fill: none; stroke: var(--md-accent-fg-color, #ff6f00); stroke-width: 4;
  transform: rotate(-90deg); transform-origin: 50% 50%;
  transition: stroke-dashoffset 0.2s linear;
}
.quiz-ring.warn .quiz-ring-fg { stroke: #d32f2f; }
.quiz-ring-text { font-size: 12px; fill: var(--md-default-fg-color, #212121); }
.quiz-ring.warn .quiz-ring-text { fill: #d32f2f; font-weight: 700; }

.quiz-media { margin: 0.4rem 0 0.9rem; }
.quiz-media video, .quiz-embed {
  width: 100%; max-height: 60vh; aspect-ratio: 16 / 9; background: #000; border: 0; border-radius: 8px;
}
.quiz-options { display: grid; gap: 0.5rem; }
.quiz-option {
  text-align: left; padding: 0.6rem 0.8rem; font-size: 0.95rem;
  border: 1px solid var(--md-default-fg-color--light, #bdbdbd);
  border-radius: 8px; background: var(--md-default-bg-color, #fff); cursor: pointer;
}
.quiz-option:hover:not([disabled]) { border-color: var(--md-accent-fg-color, #ff6f00); }
.quiz-option[disabled] { cursor: default; }
.quiz-option.is-correct { border-color: #2e7d32; background: #e8f5e9; }
.quiz-option.is-wrong { border-color: #c62828; background: #ffebee; }
.quiz-feedback { margin-top: 0.8rem; font-weight: 600; }
.quiz-feedback.good { color: #2e7d32; }
.quiz-feedback.bad { color: #c62828; }
.quiz-next { margin-top: 0.9rem; }
```

- [ ] **Step 3: Собрать и проверить в браузере**

```bash
cd site && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict
```
Открыть страницу, пройти несколько вопросов:
- у вопроса с mp4-видео таймер стартует после появления кадра (не мгновенно); у текстового — сразу;
- кольцо убывает, на 10 секундах краснеет; по нулю — автоблокировка, подсвечен верный вариант, кнопка «Далее»;
- клик по верному варианту → «Верно!» зелёным; по неверному → «Неврно…» красным + зелёная подсветка верного; остальные кнопки заблокированы;
- «Далее» ведёт к следующему; на 15-м вопросе подпись кнопки «Показать результат» (нажатие пока ничего не делает — Задача 11);
- в консоли после нескольких ответов: `__quiz.state.answers.length` растёт, у элементов есть `ok`, `chosen`, `correct`, `review`.

- [ ] **Step 4: Commit**

```bash
cd "d:/ПРОЕКТЫ с Ai/Data-Light. Обучение 2 этап"
git add site/theme/quiz.js site/theme/quiz.css
git commit -m "quiz.js: экран вопроса — плеер (mp4/vk/youtube) с детекцией готовности, круговой таймер 60с, разбор ответа и кнопка «Далее»"
git push
```

---

### Task 11: `quiz.js` — экран результата: процент, вердикт, разбивка по темам, разделы для повторения

**Files:**
- Modify: `site/theme/quiz.js`
- Modify: `site/theme/quiz.css`

**Interfaces:**
- Consumes: `state.answers`, `CFG.passPercent`, `LS_KEY`.
- Produces:
  - `renderResults()` — полноценная реализация.
  - `computeScore(answers) -> { correct, percent, verdict }`.
  - `topicBreakdown(answers) -> [{ topic, misses, reviewUrl, reviewTitle }]`.
  - `reviewLink(reviewUrl) -> string` — из `04-classifier.md#anchor` делает `../04-classifier/#anchor`.
  - запись `localStorage[LS_KEY]` со списком id набора.
  - вызов `submitResults()` (Задача 12) — здесь только заглушка-хук.

- [ ] **Step 1: Реализовать `renderResults` и хелперы**

Заменить в `quiz.js` заглушку `function renderResults() {}` на:

```javascript
  function computeScore(answers) {
    var correct = answers.filter(function (a) { return a.ok; }).length;
    var percent = Math.round((correct / TOTAL) * 100);
    var verdict = percent >= (CFG.passPercent || 80) ? "Сдано" : "Не сдано";
    return { correct: correct, percent: percent, verdict: verdict };
  }

  function reviewLink(url) {
    // "04-classifier.md#anchor" -> "../04-classifier/#anchor"
    var parts = String(url).split("#");
    var file = parts[0].replace(/\.md$/, "");
    var anchor = parts[1] ? "#" + parts[1] : "";
    return "../" + file + "/" + anchor;
  }

  function topicBreakdown(answers) {
    var byTopic = {};
    answers.forEach(function (a) {
      if (a.ok) return;
      if (!byTopic[a.topic]) {
        byTopic[a.topic] = { topic: a.topic, misses: 0, reviewUrl: a.review.url, reviewTitle: a.review.title };
      }
      byTopic[a.topic].misses += 1;
    });
    return Object.keys(byTopic).map(function (k) { return byTopic[k]; })
      .sort(function (x, y) { return y.misses - x.misses; });
  }

  function persistLastIds() {
    try {
      localStorage.setItem(LS_KEY, JSON.stringify(state.set.map(function (q) { return q.id; })));
    } catch (e) { /* приватный режим — не критично */ }
  }

  function renderResults() {
    persistLastIds();
    var sc = computeScore(state.answers);
    var wrong = state.answers.filter(function (a) { return !a.ok; });
    var breakdown = topicBreakdown(state.answers);

    root.innerHTML = "";
    var card = el("div", { class: "quiz-card quiz-results" });

    card.appendChild(el("h2", { text: "Результат" }));
    var verdictCls = sc.verdict === "Сдано" ? "pass" : "fail";
    card.appendChild(el("div", { class: "quiz-verdict " + verdictCls, text: sc.verdict }));
    card.appendChild(el("p", {
      class: "quiz-score",
      text: sc.percent + "% — верных ответов " + sc.correct + " из " + TOTAL
    }));
    card.appendChild(el("p", { class: "quiz-fio-line", text: state.surname + " " + state.name }));

    if (breakdown.length) {
      card.appendChild(el("h3", { text: "Что повторить" }));
      var table = el("table", { class: "quiz-breakdown" });
      var thead = el("tr", {}, [
        el("th", { text: "Тема" }), el("th", { text: "Ошибок" }), el("th", { text: "Раздел" })
      ]);
      table.appendChild(el("thead", {}, [thead]));
      var tbody = el("tbody");
      breakdown.forEach(function (row) {
        var link = el("a", { href: reviewLink(row.reviewUrl), text: row.reviewTitle });
        tbody.appendChild(el("tr", {}, [
          el("td", { text: row.topic }),
          el("td", { text: String(row.misses) }),
          el("td", {}, [link])
        ]));
      });
      table.appendChild(tbody);
      card.appendChild(table);
    } else {
      card.appendChild(el("p", { class: "quiz-feedback good", text: "Ошибок нет — повторять нечего." }));
    }

    if (wrong.length) {
      card.appendChild(el("h3", { text: "Разбор неверных ответов" }));
      var ul = el("ul", { class: "quiz-wrong-list" });
      wrong.forEach(function (a, i) {
        var li = el("li");
        li.appendChild(el("div", { class: "quiz-wrong-q", text: a.question }));
        li.appendChild(el("div", {
          class: "quiz-wrong-a",
          text: "Ваш ответ: " + (a.chosen === null ? "— (не успели)" : a.chosen)
        }));
        li.appendChild(el("div", { class: "quiz-wrong-c", text: "Верно: " + a.correct }));
        ul.appendChild(li);
      });
      card.appendChild(ul);
    }

    var status = el("div", { class: "quiz-send-status", text: "Отправка результата…" });
    card.appendChild(status);

    var again = el("button", { type: "button", class: "quiz-btn", text: "Пройти заново" });
    again.addEventListener("click", function () { startQuiz(state.surname, state.name); });
    card.appendChild(again);

    root.appendChild(card);

    submitResults(sc, wrong, status);
  }
```

- [ ] **Step 2: Добавить стили результата в `site/theme/quiz.css`**

```css
.quiz-verdict {
  display: inline-block; padding: 0.25rem 0.9rem; border-radius: 999px;
  font-weight: 700; font-size: 1rem; margin-bottom: 0.5rem;
}
.quiz-verdict.pass { background: #e8f5e9; color: #2e7d32; }
.quiz-verdict.fail { background: #ffebee; color: #c62828; }
.quiz-score { font-size: 1.15rem; font-weight: 600; margin: 0.3rem 0; }
.quiz-fio-line { color: var(--md-default-fg-color--light, #757575); margin-top: 0; }
.quiz-breakdown { border-collapse: collapse; width: 100%; margin: 0.4rem 0 1rem; }
.quiz-breakdown th, .quiz-breakdown td {
  border: 1px solid var(--md-default-fg-color--lightest, #e0e0e0);
  padding: 0.4rem 0.6rem; text-align: left; font-size: 0.9rem;
}
.quiz-wrong-list { padding-left: 1.1rem; }
.quiz-wrong-list li { margin-bottom: 0.7rem; }
.quiz-wrong-q { font-weight: 600; }
.quiz-wrong-a { color: #c62828; }
.quiz-wrong-c { color: #2e7d32; }
.quiz-send-status { margin: 0.8rem 0; font-size: 0.85rem; color: var(--md-default-fg-color--light, #757575); }
```

Также в этой задаче добавить временную заглушку submit (полноценно — Задача 12). Найти в `quiz.js`:
```javascript
  function submitResults() {}  // Задача 12
```
Заменить на:
```javascript
  function submitResults(sc, wrong, statusEl) {
    // Полная реализация — Задача 12. Пока просто сообщаем, что отправка не настроена.
    statusEl.textContent = "Отправка результата будет настроена (Задача 12).";
  }
```

- [ ] **Step 3: Собрать и проверить в браузере**

```bash
cd site && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict
```
Пройти тест целиком (можно быстро — отвечать наугад):
- на экране результата: вердикт-бейдж (Сдано/Не сдано), строка «NN% — верных ответов X из 15», ФИО;
- таблица «Что повторить» — только темы, где были ошибки, отсортированы по числу ошибок; ссылки открывают нужный раздел мануала (проверить 1–2 клика — якорь долистывает);
- список «Разбор неверных ответов» — вопрос, ваш ответ (или «— (не успели)»), верный;
- «Пройти заново» стартует новый набор с тем же ФИО;
- после «Пройти заново» новый набор почти не пересекается с прошлым (в консоли сравнить `__quiz.state.set.map(q=>q.id)` до и после).

- [ ] **Step 4: Commit**

```bash
cd "d:/ПРОЕКТЫ с Ai/Data-Light. Обучение 2 этап"
git add site/theme/quiz.js site/theme/quiz.css
git commit -m "quiz.js: экран результата — процент, вердикт по порогу, разбивка по темам со ссылками, разбор неверных, запись набора в localStorage"
git push
```

---

### Task 12: `quiz.js` — отправка итогов в Google-таблицу + `apps-script.gs` + инструкция

**Files:**
- Modify: `site/theme/quiz.js`
- Create: `site/quiz/apps-script.gs`
- Create: `docs/quiz-apps-script.md`

**Interfaces:**
- Consumes: `CFG.endpoint`, `CFG.token`, `state`, `computeScore`, результат прохождения.
- Produces:
  - `submitResults(sc, wrong, statusEl)` — один `fetch` POST на `CFG.endpoint`, тело — JSON строкой, `Content-Type: text/plain`. Гард от повторной отправки. Обновляет `statusEl`.
  - `buildPayload(sc, wrong) -> object`.
  - `apps-script.gs` — `doPost(e)`, дописывающий строку в лист «Результаты».

- [ ] **Step 1: Реализовать `submitResults` и `buildPayload` в `quiz.js`**

Заменить заглушку `submitResults` из Задачи 11 на:

```javascript
  function buildPayload(sc, wrong) {
    return {
      token: CFG.token || "",
      startedAt: new Date(state.startedAt).toISOString(),
      finishedAt: new Date().toISOString(),
      durationSec: Math.round((Date.now() - state.startedAt) / 1000),
      surname: state.surname,
      name: state.name,
      percent: sc.percent,
      correct: sc.correct,
      total: TOTAL,
      verdict: sc.verdict,
      wrongAnswers: wrong.map(function (a, i) {
        return {
          n: i + 1,
          question: a.question,
          chosen: a.chosen,
          correct: a.correct,
          topic: a.topic,
          reviewUrl: a.review.url
        };
      }),
      questionIds: state.set.map(function (q) { return q.id; }),
      userAgent: navigator.userAgent
    };
  }

  var _sent = false;
  function submitResults(sc, wrong, statusEl) {
    if (_sent) return;
    _sent = true;

    if (!CFG.endpoint) {
      statusEl.className = "quiz-send-status warn";
      statusEl.textContent = "Отправка результата не настроена. Сделайте скриншот этого экрана и пришлите куратору.";
      return;
    }

    fetch(CFG.endpoint, {
      method: "POST",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify(buildPayload(sc, wrong)),
      keepalive: true
    }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      statusEl.className = "quiz-send-status ok";
      statusEl.textContent = "Результат отправлен.";
    }).catch(function () {
      statusEl.className = "quiz-send-status warn";
      statusEl.textContent = "Не удалось отправить результат автоматически. Сделайте скриншот этого экрана и пришлите куратору.";
    });
  }
```

Добавить в `quiz.css`:
```css
.quiz-send-status.ok { color: #2e7d32; }
.quiz-send-status.warn { color: #c62828; font-weight: 600; }
```

- [ ] **Step 2: Создать `site/quiz/apps-script.gs`**

```javascript
/**
 * Приёмник результатов тестирования по 2 этапу.
 * Разворачивается как веб-приложение (Расширения → Apps Script в целевой Google-таблице).
 * Инструкция: docs/quiz-apps-script.md
 */

// Должен совпадать с token в site/theme/quiz-config.js
var TOKEN = 'avatar-stage2-quiz';
var SHEET_NAME = 'Результаты';

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    if (String(data.token) !== TOKEN) {
      return _json({ ok: false, error: 'bad token' });
    }
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sh = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
    if (sh.getLastRow() === 0) {
      sh.appendRow([
        'Дата и время', 'Фамилия', 'Имя', 'Процент', 'Верных из 15',
        'Вердикт', 'Неверные ответы', 'Длительность, сек', 'ID вопросов'
      ]);
    }
    var wrong = (data.wrongAnswers || []).map(function (w) {
      var chosen = (w.chosen === null || w.chosen === undefined) ? '— (не успел)' : w.chosen;
      return w.n + '. ' + w.question +
        '\n   выбрано: ' + chosen +
        '\n   верно: ' + w.correct +
        '\n   раздел: ' + w.reviewUrl;
    }).join('\n\n');

    sh.appendRow([
      new Date(),
      data.surname || '',
      data.name || '',
      data.percent,
      data.correct,
      data.verdict || '',
      wrong,
      data.durationSec,
      (data.questionIds || []).join(', ')
    ]);
    return _json({ ok: true });
  } catch (err) {
    return _json({ ok: false, error: String(err) });
  }
}

function _json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
```

- [ ] **Step 3: Создать `docs/quiz-apps-script.md`**

```markdown
# Приём результатов тестирования в Google-таблицу

Страница `manual-2-etap/07-testirovanie.md` при завершении теста шлёт один POST-запрос с
результатом. Принимает его небольшой скрипт Google Apps Script, привязанный к вашей
Google-таблице, и дописывает строку на лист «Результаты».

## Разовая настройка (≈10 минут, нужен только Google-аккаунт)

1. Создайте новую Google-таблицу (`sheets.new`). Название — любое, например
   «Аватар — тестирование 2 этап».
2. В таблице: меню **Расширения → Apps Script**. Откроется редактор скрипта.
3. Удалите содержимое файла `Код.gs` и вставьте туда полностью код из
   `site/quiz/apps-script.gs` (в этом репозитории).
4. При необходимости поменяйте константу `TOKEN` — это должна быть **та же строка**, что в
   `site/theme/quiz-config.js` (поле `token`). По умолчанию обе равны `avatar-stage2-quiz`.
5. Сохраните (значок дискеты).
6. Нажмите **Развернуть → Новое развёртывание**. Тип — **Веб-приложение**. Параметры:
   - «Описание» — любое;
   - «Запуск от имени» — **От моего имени**;
   - «У кого есть доступ» — **У всех** (или «У всех, у кого есть ссылка»).
7. Нажмите **Развернуть**, подтвердите доступы (Google спросит разрешение — это ваш
   собственный скрипт, соглашайтесь).
8. Скопируйте **URL веб-приложения** — он выглядит как
   `https://script.google.com/macros/s/XXXXXXXX/exec`.
9. Пришлите этот URL — он будет вставлен в `site/theme/quiz-config.js` (поле `endpoint`),
   и после ближайшего деплоя отправка заработает.

## Проверка (после того, как URL вставлен и сайт задеплоен)

Быстрый тест из терминала (подставьте свой URL):

```bash
curl -L -X POST 'https://script.google.com/macros/s/XXXXXXXX/exec' \
  -H 'Content-Type: text/plain;charset=utf-8' \
  --data '{"token":"avatar-stage2-quiz","surname":"Тест","name":"Проверка","percent":80,"correct":12,"total":15,"verdict":"Сдано","durationSec":300,"wrongAnswers":[{"n":1,"question":"Пример вопроса","chosen":"А","correct":"Б","topic":"Сегменты","reviewUrl":"02-segments.md#определение-и-границы"}],"questionIds":["x","y"]}'
```

Ожидается ответ `{"ok":true}` и новая строка на листе «Результаты».

## Обновление скрипта в будущем

Если правите `apps-script.gs` — в редакторе Apps Script вставьте новый код и сделайте
**Развернуть → Управление развёртываниями → (карандаш) → Версия: Новая → Развернуть**.
URL при этом не меняется.
```

- [ ] **Step 4: Собрать и проверить фолбэк-ветку**

```bash
cd site && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict -f mkdocs-public.yml
```
Открыть страницу (в `quiz-config.js` `endpoint` пока пустой):
- пройти тест до конца → в блоке статуса «Отправка результата не настроена. Сделайте скриншот…»;
- на экране всё видно (проценты, вердикт, темы, разбор) — экран самодостаточен без сервера;
- в консоли `JSON.stringify(__quiz)` не нужен, но `_sent` защищает от повторной отправки: повторный `renderResults()` вручную не шлёт второй раз (проверять не обязательно).
- проверить, что `docs/` и `site/quiz/` не попали в сборку: `ls ../../avatar-manual-build/build/quiz 2>/dev/null` — пусто; `docs/` в `exclude_docs` уже есть.

- [ ] **Step 5: Commit**

```bash
cd "d:/ПРОЕКТЫ с Ai/Data-Light. Обучение 2 этап"
git add site/theme/quiz.js site/theme/quiz.css site/quiz/apps-script.gs docs/quiz-apps-script.md
git commit -m "Тестирование 2 этапа: отправка итогов в Google-таблицу (fetch POST + фолбэк), скрипт Apps Script doPost и инструкция по публикации"
git push
```

---

### Task 13: Финальная проверка, PDF-исключение, прогон end-to-end

**Files:**
- Modify: `site/mkdocs-pdf.yml` (`plugins → print-site → exclude`)
- (при необходимости мелкие правки `quiz.css` / `quiz.js` по итогам ручной проверки)

**Interfaces:**
- Ничего нового не экспортирует. Задача — свести концы: PDF не тянет интерактивную страницу в печать, все три сборки зелёные, полный ручной прогон.

- [ ] **Step 1: Исключить страницу теста из PDF-печати**

В `site/mkdocs-pdf.yml` найти:
```yaml
      exclude:
        - index.md
```
Заменить на:
```yaml
      exclude:
        - index.md
        - manual-2-etap/07-testirovanie.md
```

- [ ] **Step 2: Три сборки со `--strict`**

```bash
cd site
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict -f mkdocs-public.yml
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict -f mkdocs-pdf.yml
```
Expected: три exit 0, без WARNING про битые ссылки/якоря.
- `build-pdf/` — печатной страницы «Тестирование» в общем PDF-контенте нет (проверить `grep -rl "quiz-root" ../../avatar-manual-build/build-pdf/` — только сама страница `07-testirovanie/`, но не `print_page/`).

- [ ] **Step 3: Полный прогон тестов**

```bash
cd site/hooks && python -m pytest tests/ -q
```
Expected: всё зелёное. Зафиксировать итоговое число в отчёте.

- [ ] **Step 4: Ручной end-to-end на собранном сайте (десктоп)**

Открыть `../../avatar-manual-build/build/manual-2-etap/07-testirovanie/index.html`. Пройти тест дважды подряд и проверить по списку:

- [ ] пункт «🧪 Тестирование по 2 этапу» в левом меню/вкладках выделен (жирный, акцентный цвет, иконка);
- [ ] вводный блок с предупреждением «обязательно ознакомиться со всем мануалом» на месте;
- [ ] кнопка «Начать тест» неактивна без обоих полей ФИО;
- [ ] ровно 15 вопросов; среди них есть вопросы с видео и текстовые; варианты ≥ 3;
- [ ] у вопроса с видео таймер стартует после готовности ролика; у текстового — сразу;
- [ ] на 10 секундах кольцо краснеет; по нулю — авто-переход, ответ засчитан неверным, показан верный;
- [ ] верный ответ → «Верно!»; неверный → подсвечен правильный + «Неверно…»;
- [ ] «Далее» листает; на 15-м — «Показать результат»;
- [ ] экран результата: %, «верных X из 15», вердикт по порогу 80, ФИО;
- [ ] таблица «Что повторить» содержит только темы с ошибками; ссылки ведут в нужные разделы мануала и долистывают до якоря;
- [ ] «Разбор неверных ответов» перечисляет вопрос / ваш ответ / верный;
- [ ] статус отправки: без настроенного endpoint — сообщение-фолбэк;
- [ ] «Пройти заново» → новый набор, пересечение с прошлым набором маленькое (проверить в консоли).

Любые косметические баги поправить здесь же (мелкие правки `quiz.css`/`quiz.js`), затем повторить сборку.

- [ ] **Step 5: Commit**

```bash
cd "d:/ПРОЕКТЫ с Ai/Data-Light. Обучение 2 этап"
git add site/mkdocs-pdf.yml site/theme/quiz.css site/theme/quiz.js
git commit -m "Тестирование 2 этапа: страница исключена из PDF-печати, финальная сверка трёх сборок и end-to-end прогон"
git push
```

- [ ] **Step 6: Сообщить пользователю, что осталось на его стороне**

Написать пользователю:
- реализация завершена и запушена; после деплоя страница доступна по адресу
  `https://ekaterina-dl.github.io/avatar-manual/manual-2-etap/07-testirovanie/`;
- чтобы заработала запись итогов в Google-таблицу — выполнить разовую настройку по
  `docs/quiz-apps-script.md` и прислать URL веб-приложения; после вставки его в
  `site/theme/quiz-config.js` (одна строка) и деплоя отправка включится;
- до этого момента тест полностью работает, только на экране результата показывает
  «отправка не настроена — сделайте скриншот».

---

## Self-Review (выполнено при составлении плана)

**Покрытие спецификации:**
- Отдельная акцентная страница/раздел меню → Task 1 (+ Task 13 PDF).
- Вступление + поля ФИО + гейт → Task 1 (текст), Task 9 (форма и блокировка кнопки).
- 15 вопросов, 60 сек, авто-переход, «верно»/правильный ответ, «Далее» → Task 10.
- Процент, число верных, вердикт, разбивка по темам, разделы для повторения → Task 11.
- Итоги в Google-таблицу (дата, фамилия, имя, результат, неверные ответы) → Task 12.
- Уникальность набора (не повторять предыдущий) → Task 9 (`assembleSet` + `localStorage`).
- Сборка вопросов со всего актуального мануала, кроме «Обзор проекта» → Task 2 (`SOURCE_FILES`), Tasks 3–7 (источники A–F), Task 8 (сборка + проверка на живом мануале).
- Видео-вопросы «какой дефект / какой ракурс по видео», ≥3 варианта, 1 верный → Tasks 3–6, инвариант проверяется в Task 8 (`test_real_bank_every_question_wellformed`).
- Актуальность при изменении мануала → хук пересобирает банк на каждой сборке (Task 2), рецепты источника D сверяют числа с текстом страницы (Task 3).

**Заглушки:** явные временные заглушки помечены и заменяются в следующей задаче
(`renderQuestion` T9→T10, `submitResults` T11→T12). Комментарии-плейсхолдеры в `build_bank`
(`# --- Задача N: …`) заменяются построчно в Tasks 3–7. Других плейсхолдеров нет.

**Согласованность типов/имён:** `assembleSet(bank, excludeIds)`, `Answer{id,question,topic,chosen,correct,ok,review}`,
`review.url` формата `<file>.md#<anchor>` — единообразны между хуком (Python) и `quiz.js`.
`reviewLink()` — единственное место, где `.md#` превращается в `../dir/#anchor`.
`CFG.token` (JS) ↔ `TOKEN` (apps-script.gs) ↔ `token` (quiz-config.js) — одна строка,
`avatar-stage2-quiz` по умолчанию, отмечено в трёх местах.
```

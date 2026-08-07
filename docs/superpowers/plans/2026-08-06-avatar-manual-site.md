# Сайт-мануал «Аватар» (MkDocs Material) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Собрать статический сайт-мануал на MkDocs Material из существующих markdown-файлов `manual-2-etap/` и `manual-3-etap/` (без копирования и без правок самих файлов мануала), с утверждённым визуальным дизайном, автоматическим встраиванием видео, скрытием меток-источников на сайте (но не в PDF), PDF-версией и публикацией на GitHub Pages.

**Architecture:** Один MkDocs-проект в `site/`, читающий markdown напрямую из родительской директории (`docs_dir: ..`) через нативный `exclude_docs`, без символических ссылок и без плагинов копирования. Два профиля сборки (`mkdocs.yml` для сайта, `mkdocs-pdf.yml` — наследует первый через `INHERIT`) отличаются только CSS и набором плагинов, а не контентом. Два Python-хука (`on_page_markdown`) на лету оборачивают метки-источников в скрываемый `<span>` и превращают ссылки на `.mp4` в `<video>`-плеер — сам markdown в `manual-*/` этих хуков не касается и остаётся сайто-агностичным. PDF собирается через `mkdocs-print-site-plugin` (чистый Python, без WeasyPrint — на Windows это избавляет от нативных зависимостей Pango/Cairo) + Playwright для рендера HTML → PDF. Деплой — GitHub Actions → GitHub Pages при каждом push.

**Tech Stack:** Python 3.14 (уже установлен), `mkdocs`, `mkdocs-material`, `mkdocs-print-site-plugin`, `playwright` (только для PDF-скрипта), git, GitHub Actions, GitHub Pages.

## Global Constraints

- Файлы `manual-2-etap/*.md` и `manual-3-etap/*.md` **не изменяются** ради нужд сайта (кроме одного независимого от сайта исправления бага в Task 1) и не копируются — сайт читает их с текущего места.
- Каждая страница мануала должна оставаться валидной как обычный markdown-файл вне сайта (все ссылки — обычные относительные markdown-ссылки, никакого сайто-специфичного HTML в исходниках).
- Адрес сайта — технический вида `<username>.github.io/avatar-manual` (без покупки домена).
- Без адаптации под мобильный экран — вёрстка только под десктоп.
- Без пароля/логина на сайт (не индексируется поисковиками через `robots.txt` / meta-тег, но доступен по прямой ссылке).
- PDF не должен требовать WeasyPrint/GTK на Windows (исторически ломается) — только чистый Python + Playwright (у Playwright свой bundled Chromium, никаких системных библиотек ставить не нужно).

## ✅ Исправление архитектуры, найденное при выполнении Task 2

При первой реальной сборке (`mkdocs build -f site/mkdocs.yml --strict`) MkDocs 1.6.1 падает на этапе валидации конфига, ещё до применения `exclude_docs`:

```
ERROR - Config value 'site_dir': The 'site_dir' should not be within the 'docs_dir'...
```

Это безусловная проверка в самом MkDocs (`mkdocs/config/config_options.py`, класс `SiteDir`) — она не смотрит на `exclude_docs`, не отключается никаким флагом. При `docs_dir: ..` (корень проекта, чтобы читать `manual-2-etap/`/`manual-3-etap/` напрямую) **любой** `site_dir` внутри корня проекта (в т.ч. `site/build`) гарантированно ловит эту ошибку — план в исходном виде не мог быть собран. Подтверждено чтением исходника MkDocs, воспроизводится в 1.6.1.

**Решение (подтверждено пользователем):** папка сборки переносится за пределы корня проекта — на уровень выше него, рядом (а не внутрь), чтобы сохранить главное архитектурное решение плана («читаем markdown напрямую, без копирования и без симлинков» — Task 2 Architecture). Новое расположение:

- Из `site/mkdocs.yml` / `site/mkdocs-pdf.yml` (пути считаются относительно самого файла конфига, то есть от `site/`): `site_dir: ../../avatar-manual-build/build` и `../../avatar-manual-build/build-pdf` соответственно.
- Из корня проекта — то есть во всех shell-командах ниже по плану, которые выполняются с `cwd` = корень проекта (`find`, `grep`, GitHub Actions steps): `../avatar-manual-build/build` и `../avatar-manual-build/build-pdf`.
- Работает одинаково локально (итог: `<родитель проекта>/avatar-manual-build/build`) и в GitHub Actions (`actions/checkout` кладёt репозиторий в `$GITHUB_WORKSPACE`, тот же относительный путь уводит за его пределы, но всё ещё внутри `runner`-workspace — писать туда можно).
- Все упоминания `site/build`/`site/build-pdf` ниже по плану заменены на новые пути. `.gitignore` из Task 1 уже закоммичен со старыми путями (`/site/build/`, `/site/build-pdf/`) — они безвредны (просто ничего не будут матчить, так как эти папки больше не создаются внутри репозитория), переделывать Task 1 не нужно.

## ⚠️ Решение, которое нужно подтвердить до Task 1 (не могу решить сам)

**Публичный или приватный репозиторий на GitHub.** Бесплатный GitHub Pages для `<username>.github.io/avatar-manual` работает "из коробки" только для **публичного** репозитория (для приватного — нужен платный план). В `_raw-sources/` лежат исходные материалы заказчика (ТЗ, служебная переписка, ОС) — по духу это внутренние документы Sber/Data Light, не предназначенные для публичного репозитория, даже несмотря на то что сама PII асессоров из них уже не публикуется. **Рекомендация (заложена в Task 1):** репозиторий публичный, но `_raw-sources/`, `_sources-log.md` обоих мануалов и `voprosy-zakazchiku.md` в git **не попадают** (только на диске, не в репозитории и не на сайте) — в публичный репозиторий и на сайт идёт только сам полированный мануал. Если нужно приватный репозиторий — скажите, тогда деплой на Pages потребует дополнительного шага (публикация только собранного `site/build` в отдельный публичный репозиторий/ветку).

> ~~Файл `example-speech-overlay.mp4.mp4` (44 МБ) без ссылок~~ — решено: это скачанный вручную
> калибровочный пример (замена неоткрывавшейся ссылки `disk.yandex.ru/i/RcmHLKFSK9bPDw`),
> переименован в `example-speech-overlay.mp4` и подключён в `11-example-library.md`. Заодно
> выяснилось важное для **Task 4**: у команды есть план скачать локально и ещё 4 длинных
> обучающих видео с Яндекс.Диска с именами вида `training-2etap-obuchenie.mp4`,
> `training-2etap-oshibki.mp4`, `training-2etap-layfhak.mp4`, `training-3etap-obuchenie.mp4`.
> Эти 4 (в отличие от `example-*`) — длинные обучающие ролики, которые по дизайну должны
> **остаться кликабельными ссылками**, а не превращаться в плеер (см. Global Constraints и
> `site/PLAN.md`: «4 длинных обучающих видео остаются кликабельными ссылками»). Task 4 ниже уже
> учитывает это правилом «пропускать файлы с именем на `training-`».

---

### Task 1: Подготовка репозитория — фикс бага, git, `.gitignore`

**Files:**
- Modify: `manual-2-etap/10-qa-log.md` (снять BOM с начала файла)
- Create: `.gitignore`
- Create: `.git/` (через `git init`)

**Interfaces:**
- Produces: git-репозиторий в корне проекта с первым коммитом, чистый от BOM файл `10-qa-log.md`, из которого дальнейшие задачи читают контент.

- [ ] **Шаг 1: Проверить BOM**

Run: `xxd "manual-2-etap/10-qa-log.md" | head -1`
Expected (текущее, баг): `00000000: efbb bf23 20d0 96d1 83d1 ...` (байты `ef bb bf` — это BOM перед `# `)

- [ ] **Шаг 2: Снять BOM**

```bash
python3 -c "
path = 'manual-2-etap/10-qa-log.md'
data = open(path, 'rb').read()
if data.startswith(b'\xef\xbb\xbf'):
    data = data[3:]
    open(path, 'wb').write(data)
    print('BOM removed')
else:
    print('no BOM found')
"
```

- [ ] **Шаг 3: Проверить, что BOM снят и первая строка — чистый заголовок**

Run: `xxd "manual-2-etap/10-qa-log.md" | head -1`
Expected: `00000000: 2320 d096 d183 d180 d0bd d0b0 d0bb 20d0` (начинается сразу с `23 20` = `# `, без `ef bb bf`)

- [ ] **Шаг 4: Создать `.gitignore` в корне проекта**

```
# Служебные материалы — не публикуются в репозитории
/_raw-sources/
/voprosy-zakazchiku.md
/manual-2-etap/_sources-log.md
/manual-3-etap/_sources-log.md

# Сборка сайта — генерируется заново каждый раз
/site/build/
/site/build-pdf/
/site/*.pdf

# Служебные файлы окружения
__pycache__/
*.pyc
.DS_Store
```

- [ ] **Шаг 5: Инициализировать git и сделать первый коммит**

```bash
git init
git add .
git status
```

Expected: в выводе `git status` НЕ должно быть файлов из `_raw-sources/`, `_sources-log.md`, `voprosy-zakazchiku.md` — если они появились, `.gitignore` написан неверно, нужно поправить перед коммитом.

```bash
git commit -m "Начальный коммит: мануал 2 и 3 этапа без служебных материалов"
```

- [ ] **Шаг 6: Проверить, что мусор не закоммичен**

Run: `git ls-files | grep -c "_raw-sources"`
Expected: `0`

Run: `git ls-files | grep -E "_sources-log|voprosy-zakazchiku"`
Expected: пустой вывод (ничего не найдено)

---

### Task 2: Скелет MkDocs + Material, полная навигация

**Files:**
- Create: `site/requirements.txt`
- Create: `site/mkdocs.yml`
- Create: `site/home/index.md`

**Interfaces:**
- Consumes: git-репозиторий из Task 1 (чистый `10-qa-log.md`).
- Produces: рабочий `mkdocs build -f site/mkdocs.yml`, кладущий готовый сайт в `../avatar-manual-build/build/` (за пределами корня проекта — см. «✅ Исправление архитектуры» в начале плана), с полной навигацией по обоим мануалам.

- [ ] **Шаг 1: Создать `site/requirements.txt`**

```
mkdocs>=1.6
mkdocs-material>=9.5
mkdocs-print-site-plugin>=2.5
```

- [ ] **Шаг 2: Установить зависимости**

```bash
python3 -m pip install -r site/requirements.txt
```

Run: `python3 -m mkdocs --version`
Expected: строка вида `mkdocs, version 1.6.x from ...` (без ошибок импорта)

- [ ] **Шаг 3: Создать домашнюю страницу `site/home/index.md`**

```markdown
# Мануал асессора «Аватар»

Проект состоит из двух независимых этапов с разными классификаторами и правилами.
Выберите свой этап:

## [2 этап →](../manual-2-etap/00-overview.md)

Заявки 26, 27, 28. Поиск подходящего сегмента внутри длинного видео.

## [3 этап →](../manual-3-etap/00-overview.md)

Заявка 46. Классификация уже нарезанного фрагмента целиком.

---

Не уверены, какой у вас этап? Спросите руководителя проекта — интерфейс разметки и
классификатор у этапов разные, важно не перепутать.
```

- [ ] **Шаг 4: Создать `site/mkdocs.yml`**

```yaml
site_name: Мануал асессора «Аватар»
site_dir: ../../avatar-manual-build/build
docs_dir: ..

exclude_docs: |
  _raw-sources/
  README.md
  voprosy-zakazchiku.md
  manual-2-etap/_sources-log.md
  manual-3-etap/_sources-log.md
  site/PLAN.md
  site/requirements.txt
  site/mkdocs.yml
  site/mkdocs-pdf.yml
  site/theme/
  site/hooks/
  site/pdf/
  docs/
  .git/
  .github/

theme:
  name: material
  custom_dir: theme/overrides
  language: ru
  palette:
    primary: white
    accent: amber
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.indexes
    - search.suggest
    - search.highlight
    - content.code.copy

extra_css:
  - theme/extra.css

nav:
  - Главная: site/home/index.md
  - 2 этап:
      - Обзор проекта: manual-2-etap/00-overview.md
      - Общие требования: manual-2-etap/01-general-requirements.md
      - Сегменты: manual-2-etap/02-segments.md
      - Качество видео: manual-2-etap/03-video-quality.md
      - Классификатор: manual-2-etap/04-classifier.md
      - Что размечаем: manual-2-etap/05-what-to-label.md
      - Частые ошибки: manual-2-etap/06-common-mistakes.md
      - FAQ: manual-2-etap/07-faq.md
      - Лайфхаки: manual-2-etap/08-lifehacks.md
      - Спорные моменты: manual-2-etap/09-disputed-points.md
      - Журнал проверок ОС: manual-2-etap/10-qa-log.md
      - Банк примеров: manual-2-etap/11-example-library.md
  - 3 этап:
      - Обзор проекта: manual-3-etap/00-overview.md
      - Общие правила: manual-3-etap/06-general-requirements.md
      - Классификатор: manual-3-etap/01-classifier.md
      - Критерии качества: manual-3-etap/04-video-quality.md
      - Банк примеров: manual-3-etap/07-example-library.md
      - Открытые вопросы: manual-3-etap/02-open-questions.md
      - Частые ошибки: manual-3-etap/03-common-mistakes.md
      - Разбор кейсов (FAQ): manual-3-etap/05-faq.md

markdown_extensions:
  - tables
  - attr_list
  - md_in_html
  - toc:
      permalink: true
```

- [ ] **Шаг 5: Создать пустой `site/theme/extra.css` (заполнится в Task 5) и пустую папку `site/theme/overrides/`**

```bash
mkdir -p site/theme/overrides
touch site/theme/extra.css
```

- [ ] **Шаг 6: Собрать сайт в строгом режиме — это и есть тест на битые ссылки/nav**

Run: `python3 -m mkdocs build -f site/mkdocs.yml --strict`
Expected: команда завершается без ошибок (exit code 0), без строк `WARNING - Doc file ... contains a link ... which is not found`. Если такие warning'и есть — значит где-то в мануале ссылка ведёт на файл, которого нет в `nav`/`exclude_docs`-области; нужно поправить `exclude_docs` или `nav`, а не сам мануал.

- [ ] **Шаг 7: Проверить, что служебные файлы не попали в собранный сайт**

Run: `find ../avatar-manual-build/build -iname "*sources-log*" -o -iname "*raw-sources*"`
Expected: пустой вывод

- [ ] **Шаг 8: Коммит**

```bash
git add site/requirements.txt site/mkdocs.yml site/home/ site/theme/
git commit -m "MkDocs Material: скелет сайта, полная навигация по обоим мануалам"
```

---

### Task 3: Хук скрытия меток-источников (видно в PDF, скрыто на сайте)

**Files:**
- Create: `site/hooks/wrap_source_tags.py`
- Modify: `site/mkdocs.yml` (добавить `hooks:`)

**Interfaces:**
- Consumes: markdown-текст страниц мануала, где метки источников выглядят как `` `[Что-то, дата]` `` — то есть текст в квадратных скобках внутри inline-код-обёртки (обратные кавычки). Пример реальной строки из мануала: `` `[Инстр. Kandinsky-Аватар, стр.1]` ``.
- Produces: в готовом HTML каждая такая метка обёрнута в `<span class="source-tag">[...]</span>` — остальной хук (Task 5, CSS) решает, показывать её или нет.

- [ ] **Шаг 1: Написать хук**

```python
# site/hooks/wrap_source_tags.py
import re

# Ищет `[любой текст без обратных кавычек и квадратных скобок внутри]`
SOURCE_TAG_RE = re.compile(r"`(\[[^\]\[`]+\])`")


def on_page_markdown(markdown, page, config, files):
    """Оборачивает метки-источники вида `[Инстр., стр.1]` в HTML-span
    с классом source-tag, чтобы CSS мог их прятать на сайте и показывать в PDF.
    Сам файл мануала при этом не меняется — обёртка происходит только на лету
    при сборке.
    """
    def replace(match):
        tag_text = match.group(1)
        return f'<span class="source-tag">{tag_text}</span>'

    return SOURCE_TAG_RE.sub(replace, markdown)
```

- [ ] **Шаг 2: Подключить хук в `site/mkdocs.yml`**

Добавить в конец `site/mkdocs.yml` (после `markdown_extensions:`):

```yaml
hooks:
  - hooks/wrap_source_tags.py
```

- [ ] **Шаг 3: Временно сделать метку видимой (по умолчанию без CSS — span ничем не отличается от обычного текста) и собрать**

Run: `python3 -m mkdocs build -f site/mkdocs.yml --strict`
Expected: exit code 0, без ошибок.

- [ ] **Шаг 4: Проверить, что конкретная метка обёрнута в span**

Run: `grep -o '<span class="source-tag">\[Инстр[^<]*</span>' ../avatar-manual-build/build/manual-2-etap/01-general-requirements/index.html | head -1`
Expected: непустая строка вида `<span class="source-tag">[Инстр. Kandinsky-Аватар, стр.1]</span>`

- [ ] **Шаг 5: Коммит**

```bash
git add site/hooks/wrap_source_tags.py site/mkdocs.yml
git commit -m "Хук: обернуть метки-источников в <span class=source-tag> для управления видимостью через CSS"
```

---

### Task 4: Хук авто-встраивания видео (`.mp4` → плеер, остальное — обычная ссылка)

**Files:**
- Create: `site/hooks/embed_local_media.py`
- Modify: `site/mkdocs.yml` (добавить хук в список `hooks:`)

**Interfaces:**
- Consumes: обычные markdown-ссылки `[текст](путь.mp4)` — как на локальные файлы (`assets/example-1.mp4`), так и на внешние (`https://.../456239217.mp4`).
- Produces: HTML `<video controls preload="metadata" src="...">` вместо `<a href="...">` для любой ссылки, путь которой заканчивается на `.mp4`, **кроме** файлов, чьё имя начинается с `training-` (длинные обучающие видео — по дизайну остаются кликабельными ссылками, см. `site/PLAN.md`). Ссылки без `.mp4` на конце (в т.ч. все ссылки на `disk.yandex.ru/i/...` — они НЕ оканчиваются на `.mp4`) тоже не трогаются.

- [ ] **Шаг 1: Написать хук**

```python
# site/hooks/embed_local_media.py
import re

# [текст](путь-или-url.mp4) — ровно markdown-ссылка, ведущая на файл с расширением .mp4
MP4_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+\.mp4)\)")

# Длинные обучающие видео (скачаны локально под этим префиксом) — по дизайну должны
# оставаться кликабельными ссылками, а не превращаться в плеер. См. site/PLAN.md:
# "4 длинных обучающих видео остаются кликабельными ссылками, не встраиваются плеером".
LONG_TRAINING_VIDEO_PREFIX = "training-"


def on_page_markdown(markdown, page, config, files):
    """Превращает markdown-ссылки на .mp4 (локальные assets/ или внешние sbercloud)
    во встроенный HTML5-плеер. Не трогает: (1) ссылки, не оканчивающиеся на .mp4
    (например, все disk.yandex.ru/i/... — это share-страницы, а не прямые файлы);
    (2) локальные файлы с именем на training- (длинные обучающие видео) — они
    остаются обычными кликабельными ссылками, как и задумано в дизайне.
    """
    def replace(match):
        alt_text, src = match.group(1), match.group(2)
        filename = src.rsplit("/", 1)[-1]
        if filename.startswith(LONG_TRAINING_VIDEO_PREFIX):
            return match.group(0)
        return (
            f'<video controls preload="metadata" style="max-width:100%">'
            f'<source src="{src}" type="video/mp4">'
            f'{alt_text}</video>'
        )

    return MP4_LINK_RE.sub(replace, markdown)
```

- [ ] **Шаг 2: Подключить хук (порядок важен — метки-источники сначала, видео потом, они не пересекаются по regex, но держим предсказуемый порядок)**

`site/mkdocs.yml`, секция `hooks:` должна стать:

```yaml
hooks:
  - hooks/wrap_source_tags.py
  - hooks/embed_local_media.py
```

- [ ] **Шаг 3: Собрать**

Run: `python3 -m mkdocs build -f site/mkdocs.yml --strict`
Expected: exit code 0.

- [ ] **Шаг 4: Проверить локальное видео стало плеером**

Run: `grep -o '<video[^>]*><source src="assets/example-1.mp4"[^>]*>' ../avatar-manual-build/build/manual-3-etap/07-example-library/index.html`
Expected: непустая строка (в файле `manual-3-etap/07-example-library.md` есть ссылка `[example-1.mp4](assets/example-1.mp4)`).

- [ ] **Шаг 5: Проверить, что ссылка на Яндекс.Диск НЕ стала плеером (осталась обычной ссылкой)**

Run: `grep -o '<a[^>]*disk.yandex.ru/i/6WmBFAJtREVl4w[^>]*>' ../avatar-manual-build/build/manual-2-etap/00-overview/index.html`
Expected: непустая строка вида `<a href="https://disk.yandex.ru/i/6WmBFAJtREVl4w">` — обычный `<a>`, не `<video>`.

- [ ] **Шаг 6: Проверить исключение для длинных обучающих видео (`training-*`), даже если файла ещё нет на диске**

На момент сборки сайта файлов `training-*.mp4` в `assets/` может ещё не быть (их скачивание — отдельная, независимая от сайта задача), поэтому проверяем саму логику хука напрямую, синтетическим примером:

```bash
python3 -c "
import sys
sys.path.insert(0, 'site/hooks')
from embed_local_media import on_page_markdown

md = '[training-2etap-obuchenie.mp4](assets/training-2etap-obuchenie.mp4)'
result = on_page_markdown(md, None, None, None)
assert result == md, f'Ожидали, что ссылка на training- не изменится, получили: {result}'
print('OK: training- ссылка не превращена в плеер')
"
```

Expected: `OK: training- ссылка не превращена в плеер` (без `AssertionError`)

- [ ] **Шаг 7: Коммит**

```bash
git add site/hooks/embed_local_media.py site/mkdocs.yml
git commit -m "Хук: автоматическое встраивание .mp4-ссылок как видео-плееров"
```

---

### Task 5: Визуальная тема — шрифты, цвета, компактные компоненты

**Files:**
- Modify: `site/theme/extra.css`

**Interfaces:**
- Consumes: собранный HTML из Task 2-4 (стандартная разметка Material + `<span class="source-tag">` из Task 3).
- Produces: применённые шрифты Golos Text/PT Serif, тёплый янтарный акцент, холодные нейтральные серые, зелёно-красная пара для таблиц «Правильно/Неправильно», скрытые на сайте метки-источников.

**Область этой задачи (осознанно, без лишнего):** база типографики и цвета, скрытие меток-источников, подсветка уже существующих в мануале таблиц-сравнений «Правильно/Неправильно» зелёным/красным. Карточки-факты, иконки вместо точек списка и zoom-сетка примеров — в блоке «Отложено» в конце плана: это точечные визуальные улучшения конкретных страниц, а не инфраструктура, их разумнее делать после того, как сайт уже опубликован и виден вживую.

**См. также `site/prototype-reference/`** — сохранённый код живого макета, на котором дизайн
был утверждён с пользователем (точные CSS-переменные для всех цветов/тем, готовые файлы
шрифтов, CSS всех отложенных на Phase 2 компонентов). Значения ниже в этом Task уже сверены
с ним; при реализации Phase 2 — брать оттуда, не придумывать заново.

- [ ] **Шаг 1: Написать `site/theme/extra.css`**

```css
/* Шрифты: Golos Text для заголовков/интерфейса, PT Serif для основного текста */
@import url('https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;500;600;700&family=PT+Serif:wght@400;700&display=swap');

:root {
  /* Тёплый янтарный акцент — точное значение с утверждённого макета,
     см. site/prototype-reference/README.md */
  --md-accent-fg-color: #B96A22;

  /* Холодные нейтральные серые (slate-подобная шкала) */
  --gray-50: #F8FAFC;
  --gray-100: #F1F5F9;
  --gray-300: #CBD5E1;
  --gray-600: #475569;
  --gray-900: #0F172A;

  /* Зелёно-красная пара — только для «допустимо/недопустимо»,
     точные значения с утверждённого макета */
  --ok-color: #2E7D4F;
  --ok-bg: rgba(46, 125, 79, 0.09);
  --no-color: #B23B32;
  --no-bg: rgba(178, 59, 50, 0.08);
}

body, .md-typeset {
  font-family: 'PT Serif', Georgia, serif;
}

.md-typeset h1,
.md-typeset h2,
.md-typeset h3,
.md-typeset h4,
.md-header,
.md-nav,
.md-tabs {
  font-family: 'Golos Text', -apple-system, sans-serif;
}

/* Метки-источников: скрыты на сайте, видны в PDF-профиле (там это правило
   переопределяется в site/pdf/pdf-extra.css из Task 6) */
.source-tag {
  display: none;
}

/* Видео-плеер, вставленный хуком из Task 4 */
.md-typeset video {
  display: block;
  margin: 1em 0;
  border-radius: 4px;
  border: 1px solid var(--gray-300);
}

```

Подсветку зелёным/красным конкретно таблиц «Правильно/Неправильно» нельзя сделать чистым
CSS-селектором (стандартного `:contains()` по тексту ячейки не существует, это только
jQuery-расширение) — делаем маленьким JS-сниппетом, который находит нужные таблицы по
точному тексту заголовков и навешивает классы `.compare-ok`/`.compare-no`; CSS-правило для
этих классов добавляется тут же, следующим шагом, вместе с самим JS.

- [ ] **Шаг 2: Добавить маленький JS для подсветки compare-таблиц (найти по точному тексту заголовка, не по классу — markdown не меняем)**

Создать `site/theme/compare-tables.js`:

```javascript
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".md-typeset table").forEach(function (table) {
    var headers = table.querySelectorAll("thead th");
    if (headers.length === 2) {
      var first = headers[0].textContent.trim();
      var second = headers[1].textContent.trim();
      if (first === "Правильно" && second === "Неправильно") {
        table.classList.add("compare-table");
        var firstCol = table.querySelectorAll("tbody td:first-child");
        var secondCol = table.querySelectorAll("tbody td:last-child");
        firstCol.forEach(function (td) { td.classList.add("compare-ok"); });
        secondCol.forEach(function (td) { td.classList.add("compare-no"); });
      }
    }
  });
});
```

Добавить в `site/mkdocs.yml` после `extra_css:`:

```yaml
extra_javascript:
  - theme/compare-tables.js
```

Добавить в конец `site/theme/extra.css`:

```css
.compare-ok {
  background: var(--ok-bg);
  border-left: 3px solid var(--ok-color);
}
.compare-no {
  background: var(--no-bg);
  border-left: 3px solid var(--no-color);
}
```

- [ ] **Шаг 3: Собрать и проверить, что шрифты и цвет подключены**

Run: `python3 -m mkdocs build -f site/mkdocs.yml --strict`
Expected: exit code 0.

Run: `grep -c "Golos+Text" ../avatar-manual-build/build/manual-2-etap/00-overview/index.html`
Expected: `1` (или больше — главное, не `0`)

- [ ] **Шаг 4: Проверить, что метка-источник действительно скрыта в собранном CSS**

Run: `grep -A1 "\.source-tag" ../avatar-manual-build/build/assets/stylesheets/*.css 2>/dev/null || grep -A1 "\.source-tag" site/theme/extra.css`

(MkDocs Material инлайнит `extra_css` файлы как отдельные `<link>`, поэтому проверяем сам файл темы, а не собранный CSS-бандл Material)

Run: `grep -A1 "\.source-tag" site/theme/extra.css`
Expected:
```
.source-tag {
  display: none;
}
```

- [ ] **Шаг 5: Открыть страницу глазами (ручная проверка, т.к. это визуальный дизайн)**

Run: `python3 -m mkdocs serve -f site/mkdocs.yml` (оставить работать) и открыть `http://127.0.0.1:8000/avatar-manual/manual-2-etap/02-segments/` в браузере — глазами свериться с утверждённым макетом: шрифты, цвет ссылок/акцентов, что таблица «Правильно/Неправильно» подсвечена, что метки-источников не видно в тексте, что видео из `assets/` реально воспроизводится плеером. Остановить сервер (Ctrl+C) после проверки.

- [ ] **Шаг 6: Коммит**

```bash
git add site/theme/extra.css site/theme/compare-tables.js site/mkdocs.yml
git commit -m "Визуальная тема: шрифты Golos Text/PT Serif, цвета, скрытие меток-источников, подсветка compare-таблиц"
```

---

### Task 6: PDF-профиль сборки (метки-источников видны, отдельный CSS)

**Files:**
- Create: `site/mkdocs-pdf.yml`
- Create: `site/pdf/pdf-extra.css`

**Interfaces:**
- Consumes: `site/mkdocs.yml` из Task 2-5 (через `INHERIT`), тот же контент и те же хуки.
- Produces: `mkdocs build -f site/mkdocs-pdf.yml` кладёт в `../avatar-manual-build/build-pdf/` версию сайта, где `mkdocs-print-site-plugin` дополнительно генерирует одну большую страницу `print_page/index.html` со всем мануалом подряд, и метки-источников на ней **видны** (в отличие от обычного сайта).

- [ ] **Шаг 1: Добавить `mkdocs-print-site-plugin` в зависимости (уже добавлен в Task 2 requirements.txt — проверить)**

Run: `grep print-site site/requirements.txt`
Expected: `mkdocs-print-site-plugin>=2.5`

- [ ] **Шаг 2: Создать `site/pdf/pdf-extra.css` — переопределяет только видимость меток-источников**

```css
/* PDF-профиль: метки-источников должны быть видны (в отличие от сайта) */
.source-tag {
  display: inline;
  color: #6B7280;
  font-size: 0.85em;
  margin-left: 0.3em;
}

/* Разрыв страницы перед каждым H1 — чтобы каждая глава мануала начиналась с новой страницы */
.md-typeset h1 {
  page-break-before: always;
}
```

- [ ] **Шаг 3: Создать `site/mkdocs-pdf.yml`**

```yaml
INHERIT: mkdocs.yml
site_dir: ../../avatar-manual-build/build-pdf

extra_css:
  - theme/extra.css
  - pdf/pdf-extra.css

plugins:
  - print-site:
      add_to_navigation: true
      print_page_title: 'Весь мануал (для печати в PDF)'
      add_table_of_contents: true
      toc_depth: 2
      add_full_urls: false
      enumerate_headings: false
      enumerate_figures: false
      add_cover_page: true
      cover_page_template: ""
      path_to_pdf: ""
      exclude:
        - site/home/index.md
```

- [ ] **Шаг 4: Собрать PDF-профиль**

Run: `python3 -m mkdocs build -f site/mkdocs-pdf.yml --strict`
Expected: exit code 0, создаётся `../avatar-manual-build/build-pdf/print_page/index.html`.

- [ ] **Шаг 5: Проверить, что в PDF-профиле метка-источник видна (в отличие от сайта из Task 5)**

Run: `grep -A1 "\.source-tag" site/pdf/pdf-extra.css`
Expected:
```
.source-tag {
  display: inline;
```

Run: `grep -c "source-tag" ../avatar-manual-build/build-pdf/print_page/index.html`
Expected: число больше `0` (метки физически присутствуют в HTML — видимость управляется только CSS, который здесь другой)

- [ ] **Шаг 6: Коммит**

```bash
git add site/mkdocs-pdf.yml site/pdf/pdf-extra.css
git commit -m "PDF-профиль сборки: print-site plugin, метки-источников видны"
```

---

### Task 7: Рендер PDF-файла из print-страницы через Playwright

**Files:**
- Create: `site/pdf/render_pdf.py`
- Modify: `site/requirements.txt` (добавить `playwright`)

**Interfaces:**
- Consumes: `../avatar-manual-build/build-pdf/print_page/index.html` из Task 6.
- Produces: `../avatar-manual-build/build-pdf/Аватар-мануал.pdf` — один файл, пригодный для скачивания и печати.

- [ ] **Шаг 1: Добавить Playwright в зависимости**

Дописать в `site/requirements.txt`:
```
playwright>=1.45
```

- [ ] **Шаг 2: Установить Playwright и его браузер**

```bash
python3 -m pip install -r site/requirements.txt
python3 -m playwright install chromium
```

Run: `python3 -m playwright --version`
Expected: строка вида `Version 1.4x.x` без ошибок.

- [ ] **Шаг 3: Написать скрипт рендера**

```python
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
```

- [ ] **Шаг 4: Запустить рендер**

```bash
python3 site/pdf/render_pdf.py
```

Expected: строка `Готово: .../Аватар-мануал.pdf (... КБ)`, без traceback.

- [ ] **Шаг 5: Проверить, что PDF реально создан и не пустой**

Run: `python3 -c "import pathlib; p = pathlib.Path('../avatar-manual-build/build-pdf/Аватар-мануал.pdf'); print(p.exists(), p.stat().st_size)"`
Expected: `True <число больше 1000000>` (мануал большой, меньше мегабайта — явно что-то не так)

- [ ] **Шаг 6: Коммит**

```bash
git add site/pdf/render_pdf.py site/requirements.txt
git commit -m "PDF: скрипт рендера print-страницы в файл через Playwright"
```

(Сам файл `Аватар-мануал.pdf` не коммитим — он теперь физически лежит вне репозитория, в `../avatar-manual-build/build-pdf/` — см. «Исправление архитектуры» в начале плана, коммитить нечего в принципе. Генерируется заново при каждой сборке, в т.ч. автоматически в Task 8.)

---

### Task 8: GitHub Actions — автосборка и публикация на GitHub Pages

**Files:**
- Create: `.github/workflows/deploy.yml`

**Interfaces:**
- Consumes: весь репозиторий из Task 1-7.
- Produces: при каждом push в `main` сайт пересобирается и публикуется на `https://<username>.github.io/avatar-manual/` без ручных действий.

**Предварительно (руками, не через агента — создание репозитория на чужом аккаунте не автоматизируется отсюда):**
1. Зайти на github.com, создать **новый публичный** репозиторий с именем `avatar-manual`, **без** авто-инициализации README/`.gitignore`/лицензии (у нас уже всё своё).
2. Прислать мне (или ввести самостоятельно) HTTPS-адрes репозитория вида `https://github.com/<username>/avatar-manual.git`.
3. В настройках репозитория → Settings → Pages → Source: выбрать **GitHub Actions** (не "Deploy from a branch").

- [ ] **Шаг 1: Написать workflow**

```yaml
# .github/workflows/deploy.yml
name: Deploy avatar manual site

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r site/requirements.txt

      - name: Build site
        run: python -m mkdocs build -f site/mkdocs.yml --strict

      - uses: actions/upload-pages-artifact@v3
        with:
          path: ../avatar-manual-build/build

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Шаг 2: Добавить `robots.txt`, чтобы сайт не индексировался поисковиками (доступ по прямой ссылке, без пароля — как решено в PLAN.md)**

Создать `site/home/../robots.txt` — точнее, т.к. `docs_dir` — это корень проекта, файл нужно положить так, чтобы MkDocs скопировал его в корень собранного сайта:

```
# site/robots.txt.template — не часть nav, копируется вручную в build-шаге
```

Проще и надёжнее — добавить копирование прямо в workflow, отдельным шагом перед `upload-pages-artifact`:

```yaml
      - name: Add robots.txt (no-index)
        run: |
          printf 'User-agent: *\nDisallow: /\n' > ../avatar-manual-build/build/robots.txt
```

Вставить этот шаг в `.github/workflows/deploy.yml` между `Build site` и `actions/upload-pages-artifact@v3`.

- [ ] **Шаг 3: Локально проверить, что тот же билд-шаг проходит (workflow использует ту же команду)**

Run: `python3 -m mkdocs build -f site/mkdocs.yml --strict && printf 'User-agent: *\nDisallow: /\n' > ../avatar-manual-build/build/robots.txt && test -f ../avatar-manual-build/build/robots.txt && echo OK`
Expected: `OK`

- [ ] **Шаг 4: Закоммитить workflow**

```bash
git add .github/workflows/deploy.yml
git commit -m "GitHub Actions: автосборка и публикация на GitHub Pages при каждом push"
```

- [ ] **Шаг 5: Подключить удалённый репозиторий и запушить (репозиторий на GitHub уже должен существовать — см. предварительный шаг выше)**

```bash
git branch -M main
git remote add origin https://github.com/<username>/avatar-manual.git
git push -u origin main
```

Expected: push проходит без ошибок (при первом push git запросит аутентификацию — на Windows обычно откроется окно браузера от Git Credential Manager, нужно один раз войти в аккаунт).

- [ ] **Шаг 6: Проверить, что workflow отработал успешно**

Открыть `https://github.com/<username>/avatar-manual/actions` в браузере — последний запуск workflow "Deploy avatar manual site" должен быть зелёным (Success). Если красный — открыть лог шага, который упал, и разобраться по тексту ошибки (типичная причина — не пройденный `--strict` из-за нового битого relative-ссылки).

- [ ] **Шаг 7: Открыть сайт и проверить, что он работает**

Открыть `https://<username>.github.io/avatar-manual/` — должна открыться домашняя страница из Task 2 с двумя ссылками на этапы; перейти на любую страницу мануала, проверить поиск (иконка лупы в шапке), проверить, что хотя бы одно видео воспроизводится.

---

### Task 9: Финальная проверка

**Files:** нет изменений, только проверки.

**Interfaces:** нет — это приёмочный чек-лист по всему, что построено в Task 1-8.

- [ ] **Шаг 1: Полная проверка ссылок ещё раз с нуля (на случай, если что-то в мануале поменялось за время сборки сайта)**

```bash
python3 -m mkdocs build -f site/mkdocs.yml --strict
python3 -m mkdocs build -f site/mkdocs-pdf.yml --strict
```

Expected: оба — exit code 0.

- [ ] **Шаг 2: Проверить приватность в собранном HTML (тот же список паттернов, что использовался в аудитах мануала)**

```bash
grep -rEl "@(yandex\.ru|mail\.ru|gmail\.com|inbox\.ru|internet\.ru|vk\.com|list\.ru)" ../avatar-manual-build/build/ ../avatar-manual-build/build-pdf/ 2>/dev/null
```

Expected: пустой вывод (ни одного email-адреса в собранном сайте/PDF)

- [ ] **Шаг 3: Убедиться, что `_raw-sources` физически не попал ни в git, ни в сборку**

```bash
git ls-files | grep -c raw-sources
find ../avatar-manual-build/build ../avatar-manual-build/build-pdf -iname "*raw-sources*" 2>/dev/null
```

Expected: `0` и пустой вывод соответственно.

- [ ] **Шаг 4: Пересчитать PDF после всех изменений**

```bash
python3 site/pdf/render_pdf.py
```

Expected: как в Task 7 Шаг 4 — файл создан, размер разумный (не единицы КБ).

- [ ] **Шаг 5: Финальный коммит и push, если после проверок были правки**

```bash
git add -A
git commit -m "Финальная проверка сайта и PDF" --allow-empty
git push
```

---

## Что сознательно отложено (Phase 2, не блокирует запуск)

- **Карточки-факты** для ключевых цифр (например, «10–300 сек» отдельным крупным блоком) — требует прохода по каждой странице и решения, какие именно числа выделять; разумнее делать по живому сайту, а не вслепую.
- **Иконки вместо точек списка** (время/запрет и т.п.) — то же самое: нужен просмотр реальных списков постранично, чтобы не расставить неправильные иконки.
- **Сетка примеров 3-4 в ряд с hover-zoom** — сейчас примеры в `11-example-library.md`/`07-example-library.md` оформлены как обычный список ссылок; чтобы сделать сетку, нужно сначала решить (с пользователем), какие именно примеры войдут в сетку и в каком визуальном виде — это дизайнерское, а не техническое решение.
- **Скачивание оставшихся длинных обучающих видео** (кроме тех, что уже расшифрованы и разобраны) — по желанию, не блокирует сайт: они и так корректно остаются кликабельными ссылками на Яндекс.Диск благодаря Task 4.
- **Self-hosting шрифтов** (вместо Google Fonts CDN) — сейчас шрифты подключены через `@import` с fonts.googleapis.com; если понадобится работать без доступа к интернету или строго без внешних запросов — можно будет скачать `.woff2` файлы в `site/theme/fonts/` и переключить `@import` на `@font-face` с локальными путями.

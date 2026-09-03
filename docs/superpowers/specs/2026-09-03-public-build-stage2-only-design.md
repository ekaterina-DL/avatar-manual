# Публичная сборка сайта: только 2 этап, 3 этап скрыт

**Дата:** 2026-09-03
**Статус:** утверждено, реализуется

## Задача

Ссылку на сайт-мануал (`https://ekaterina-dl.github.io/avatar-manual/`) пора раздать всем
асессорам 2 этапа. Мануал 3 этапа (заявка 46, папка `manual-3-etap/`) ещё в работе и наружу
пока не выкладывается — его должна видеть только автор проекта, локально.

### Что решили на этапе обсуждения

- **Пароль не подходит.** Репозиторий `ekaterina-DL/avatar-manual` — публичный, поэтому
  исходники 3 этапа (`manual-3-etap/*.md`) и так открыты на GitHub. На бесплатном GitHub Pages
  настоящего входа по паролю нет. JS-заглушка с паролем — иллюзия защиты (текст всё равно
  уезжает в браузер).
- **Секретность не критична** — задача не «спрятать текст», а «не показывать всем
  недоделанный раздел на опубликованном сайте».
- **Локального просмотра достаточно.** Работа над 3 этапом всё равно идёт локально; на
  опубликованном сайте он автору для правок не нужен.

Вывод: 3 этап просто не попадает в опубликованную сборку. Локально (`mkdocs serve`) и в
PDF-сборке сайт остаётся полным.

## Решение

Третий профиль сборки — «публичный» — по образцу уже существующего PDF-профиля
(`site/mkdocs-pdf.yml` наследует `site/mkdocs.yml` через `INHERIT` и меняет несколько ключей;
хуки различают профиль по суффиксу папки сборки — `_build_profile.is_pdf_build`).

| Профиль | Конфиг | Папка сборки | 3 этап |
|---|---|---|---|
| Сайт (локально) | `site/mkdocs.yml` | `build` | есть |
| PDF (локально) | `site/mkdocs-pdf.yml` | `build-pdf` | есть |
| **Публичный (CI → Pages)** | **`site/mkdocs-public.yml`** | **`build-public`** | **нет** |

### Изменения

1. **`site/mkdocs-public.yml`** (новый). `INHERIT: mkdocs.yml`. Переопределяет:
   - `site_dir: ../../avatar-manual-build/build-public` — сигнал профиля для хуков;
   - `exclude_docs` — добавляет `manual-3-etap/` (страницы 3 этапа не собираются вообще,
     прямые адреса `/manual-3-etap/...` дают 404);
   - `nav` — повторяет только «Главная» + «2 этап (заявки 26-28)», без раздела «3 этап».

   > Проверить при реализации: складываются ли `exclude_docs` родителя и потомка при
   > `INHERIT` в mkdocs 1.6.1. Если нет — скопировать полный список `exclude_docs` из
   > `mkdocs.yml` в `mkdocs-public.yml` и пометить комментарием, что списки должны совпадать.

2. **`site/hooks/_build_profile.py`** — добавить `is_public_build(config)`: `site_dir`
   заканчивается на `build-public`. Рядом с существующим `is_pdf_build`; суффиксы
   `build-pdf` / `build-public` / `build` взаимно не пересекаются.

3. **`site/hooks/public_drop_stage3.py`** (новый). `on_page_markdown`, no-op если
   `not is_public_build(config)`. В публичном профиле:
   - на `index.md` убирает блок «выбор этапа», относящийся к 3 этапу (заголовок-ссылка
     `## [3 этап →](manual-3-etap/00-overview.md)` и абзац под ним, до строки `---` или
     следующего заголовка). Разделитель `---` и абзац-подсказку «Не уверены, какой у вас
     этап?» сохраняет;
   - на любой странице превращает markdown-ссылки с URL в `manual-3-etap/` в обычный текст
     (видимый текст остаётся, ссылка снимается) — иначе строгая сборка (`--strict`) упадёт
     на 6 перекрёстных ссылках из страниц 2 этапа. Это ровно то, что уже делает
     `neutralize_excluded_links.py` для `_sources-log.md` / `voprosy-zakazchiku.md`.

   Регистрируется в `site/mkdocs.yml` в списке `hooks:` последним (после
   `friendly_md_link_text.py` и `neutralize_excluded_links.py`, чтобы работать по уже
   финальному markdown; сопоставление по URL, а не по видимому тексту ссылки).

4. **`site/mkdocs.yml`** — одна строка: `- hooks/public_drop_stage3.py` в конец списка
   `hooks:`. На локальную и PDF-сборку не влияет (хук там no-op).

5. **`.github/workflows/deploy.yml`** — собирать `-f site/mkdocs-public.yml`; `robots.txt`
   и `upload-pages-artifact` — из `../avatar-manual-build/build-public`.

6. **`site/hooks/tests/test_public_drop_stage3.py`** (новый) + пара кейсов в
   `test_build_profile.py`. По образцу `test_hide_site_only_sections.py`
   (Fake-Page/File/Config, кейсы «в публичной сборке», «в обычной сборке не трогает»).

### Перекрёстные ссылки 2 этап → 3 этап (гасятся хуком)

- `index.md:10` — заголовок-ссылка (убирается вместе с блоком)
- `manual-2-etap/00-overview.md` — строки 6, 74, 185, 245
- `manual-2-etap/04-classifier.md` — строка 262

После гашения читаются как обычный текст («см. мануал 3 этапа») без битой ссылки. Исходные
`.md` не меняются — замена только на лету при публичной сборке.

## Поведение после внедрения

- **Опубликованный сайт:** «Главная» (без блока 3 этапа) + вкладка «2 этап». Любой адрес
  `/manual-3-etap/...` → 404. Поиск по сайту 3 этап не находит.
- **Локально** (`mkdocs serve`, `python -m mkdocs build -f site/mkdocs.yml`): без изменений,
  весь сайт включая 3 этап.
- **PDF** (`site/mkdocs-pdf.yml`): без изменений, весь мануал.
- **Репозиторий** остаётся публичным; `manual-3-etap/*.md` по-прежнему читаются на GitHub —
  это осознанно принято.

## Как вернуть 3 этап в публикацию

Когда автор скажет «публикуем 3 этап» — сделать одно из двух:

- **Быстро:** `git revert` коммита с этими изменениями (вернёт `deploy.yml` на
  `site/mkdocs.yml`, удалит `mkdocs-public.yml` и хук). Затем убедиться, что сборка
  `site/mkdocs.yml --strict` проходит, и запушить.
- **Аккуратно (если `mkdocs.yml` с тех пор менялся):** в `.github/workflows/deploy.yml`
  вернуть `-f site/mkdocs.yml` и путь `build`; удалить `site/mkdocs-public.yml`,
  `site/hooks/public_drop_stage3.py`, строку хука из `mkdocs.yml`, `is_public_build` из
  `_build_profile.py` и тест. Проверить `python -m mkdocs build -f site/mkdocs.yml --strict`
  и `python -m pytest` в `site/hooks/`, запушить.

Отдельные правки в `manual-3-etap/*` для публикации не нужны — они всё это время
поддерживаются в рабочем состоянии обычной локальной сборкой.

## Проверка при реализации

- `python -m mkdocs build -f site/mkdocs-public.yml --strict` проходит без ошибок.
- В `avatar-manual-build/build-public/` нет каталога `manual-3-etap/`, нет `site/`,
  `.git/`, `_raw-sources/`, `docs/` и прочего из `exclude_docs`.
- `build-public/index.html` не содержит «3 этап» и ссылок на `manual-3-etap`.
- `build-public/manual-2-etap/00-overview/index.html` и `.../04-classifier/index.html`
  не содержат ссылок `href=".../manual-3-etap/..."` (текст-упоминание допустим).
- `python -m mkdocs build -f site/mkdocs.yml --strict` по-прежнему проходит и содержит
  3 этап.
- `python -m pytest` в `site/hooks/` — зелёный.

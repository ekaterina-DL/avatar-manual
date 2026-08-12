# Карточки-факты Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (Inline Execution — обоснование см. в конце документа) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить 4 карточки-факта (`.keyfacts`) в 3 файла мануала — визуальное выделение уже
присутствующих в прозе ключевых чисел, без потери и без замены самого текста.

**Architecture:** Прямые HTML-блоки в исходных markdown-файлах (через уже подключённый
`md_in_html`), без нового Python-хука — элемент дополняет текст, не заменяет его. Новый CSS
`.keyfacts` в `site/theme/extra.css` — переведённый на актуальные токены сайта компонент из уже
утверждённого макета `site/prototype-reference/template.html`. PDF-профиль скрывает карточки
через `display: none` в `site/pdf/pdf-extra.css` — тот же приём, что уже применён к градиентной
шкале и карточкам-исходам «Сегмент/Битое» (12.08.2026).

**Tech Stack:** mkdocs-material, Python-Markdown (`md_in_html`), чистый CSS.

## Global Constraints

- Ни один заголовок не переименовывается — все 4 вставки идут между уже существующими
  заголовком и следующим за ним контентом (списком/абзацем), не задевая сам текст заголовка.
- Цвета — только через существующие CSS-переменные (`--card-line`, `--gray-50`, `--card-shadow`,
  `--accent-ink`, `--gray-900`, `--gray-600`, `--no-color`, `--no-bg`) — новых токенов не
  вводится, кроме одного inline-значения границы тега (см. Task 1 Шаг 1, обоснование внутри).
- `markdown="1"` не используется ни на одном `<div>` — всё содержимое чисто текстовое, без
  markdown-разметки (тот же принцип, что уже у `.apeal-flow`/`.threshold-scale`).
- Каждое число в карточке уже присутствует в окружающей прозе того же файла — карточка ничего не
  утверждает заново, только выделяет визуально.
- Новых Python-хуков и новых pytest-тестов эта работа не создаёт — действующий набор
  (125 тестов после волны визуальной системы 3 этапа) должен остаться зелёным без изменений.
- Build-diff обоих профилей (`mkdocs.yml`/`mkdocs-pdf.yml`) через `python -m mkdocs build
  --strict` не должен добавлять новых WARNING-строк.

---

## Task 1: CSS-компонент `.keyfacts`

**Files:**
- Modify: `site/theme/extra.css` (добавить в конец файла)
- Modify: `site/pdf/pdf-extra.css` (добавить в конец файла)

**Interfaces:**
- Produces (используется Task 2 в HTML-разметке 4 файлов): классы `.keyfacts`, `.kf-stats`,
  `.kf-stat`, `.kf-value` (со вложенным `<span>` для единицы измерения), `.kf-label`,
  `.kf-forbid`, `.kf-forbid-label`, `.kf-tags`, `.kf-tag`.

- [ ] **Шаг 1: Дописать CSS в `site/theme/extra.css`**

Перейти в конец файла (после блока `.example-card .ec-verdict`/цветовых модификаторов,
добавленного волной визуальной системы 3 этапа 12.08.2026), добавить:

```css

/* Карточки-факты — визуальное выделение отдельных ключевых чисел мануала (не многоуровневых
   порогов — для тех есть .threshold-scale). Переведённый на актуальные токены сайта компонент
   .keyfacts из уже утверждённого макета site/prototype-reference/template.html (06.08.2026,
   строки 184-214) — цвета/тени 1:1 совпадают с уже реализованными переменными, кроме фона
   карточки (там был чистый белый, здесь — var(--gray-50) для согласованности с уже собранными
   карточками сайта) и иконки «нельзя» (там — inline SVG, здесь — эмодзи 🚫, как и везде на
   сайте). См. docs/superpowers/specs/2026-08-12-fact-cards-design.md. Декоративное дополнение —
   каждое число уже есть в прозе рядом, поэтому в PDF скрывается (site/pdf/pdf-extra.css). */
.keyfacts {
  border: 1px solid var(--card-line);
  border-radius: 14px;
  background: var(--gray-50);
  box-shadow: var(--card-shadow);
  padding: 22px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin: 1.4em 0;
}
.keyfacts .kf-stats {
  display: flex;
  gap: 0;
}
.keyfacts .kf-stat {
  flex: 1;
  padding-right: 24px;
}
.keyfacts .kf-stat + .kf-stat {
  padding-left: 24px;
  border-left: 1px solid var(--card-line);
}
.keyfacts .kf-value {
  font-family: 'Golos Text', sans-serif;
  font-weight: 700;
  font-size: 2.4rem;
  line-height: 1;
  color: var(--gray-900);
  font-variant-numeric: tabular-nums;
  letter-spacing: -.01em;
  display: flex;
  align-items: baseline;
  gap: 7px;
}
.keyfacts .kf-value span {
  font-size: 1rem;
  font-weight: 600;
  color: var(--accent-ink);
}
.keyfacts .kf-label {
  margin-top: 7px;
  font-size: .86rem;
  color: var(--gray-600);
  line-height: 1.4;
}
.keyfacts .kf-forbid {
  border-top: 1px solid var(--card-line);
  padding-top: 18px;
}
.keyfacts .kf-forbid-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Golos Text', sans-serif;
  font-weight: 700;
  font-size: .92rem;
  color: var(--gray-900);
  margin-bottom: 11px;
}
.keyfacts .kf-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.keyfacts .kf-tag {
  font-family: 'Golos Text', sans-serif;
  font-size: .83rem;
  font-weight: 600;
  color: var(--no-color);
  background: var(--no-bg);
  /* .32-непрозрачная версия --no-color — тот же оттенок, что уже использует --no-color/--no-bg
     пара, отдельного переменного токена под это не заводим (единственное использование). */
  border: 1px solid rgba(178, 59, 50, .32);
  border-radius: 7px;
  padding: 5px 11px;
}
@media (max-width: 480px) {
  .keyfacts .kf-stats { flex-direction: column; gap: 16px; }
  .keyfacts .kf-stat + .kf-stat {
    padding-left: 0;
    border-left: none;
    padding-top: 16px;
    border-top: 1px solid var(--card-line);
  }
}
```

- [ ] **Шаг 2: Дописать правило скрытия в `site/pdf/pdf-extra.css`**

Перейти в конец файла (после правила `.threshold-scale, .decision-outcome { display: none; }`,
добавленного волной градиентной шкалы 12.08.2026), добавить:

```css

/* Карточки-факты — декоративное дублирование чисел, уже присутствующих в прозе рядом; только
   сайт. См. docs/superpowers/specs/2026-08-12-fact-cards-design.md */
.keyfacts {
  display: none;
}
```

- [ ] **Шаг 3: Проверить, что тесты хуков не сломались**

Run: `cd site/hooks && python -m pytest tests/ -q`
Expected: `125 passed` (CSS-файлы не затрагивают Python-хуки — количество тестов не меняется).

- [ ] **Шаг 4: Коммит**

```bash
git add site/theme/extra.css site/pdf/pdf-extra.css
git commit -m "CSS-компонент .keyfacts (карточки-факты) — контента, который его использует, пока нет, стили подключены заранее (Task 1, дизайн-документ 2026-08-12-fact-cards-design.md)"
```

---

## Task 2: Вставка 4 карточек в 3 файла

**Files:**
- Modify: `manual-2-etap/02-segments.md` (2 вставки: после `## Определение и границы`, после
  `## Ограничения интерфейса`)
- Modify: `manual-2-etap/00b-exam.md` (1 вставка: после вступительной цитаты)
- Modify: `manual-3-etap/00-overview.md` (1 вставка: после `## Нормативы`)

**Interfaces:**
- Consumes: классы из Task 1 — `.keyfacts`/`.kf-stats`/`.kf-stat`/`.kf-value`/`.kf-label`/
  `.kf-forbid`/`.kf-forbid-label`/`.kf-tags`/`.kf-tag`.

- [ ] **Шаг 1: Карточка длительности сегмента — `manual-2-etap/02-segments.md`**

Текущий текст (сразу после заголовка «Определение и границы»):

```
## Определение и границы

- ⏱️ **Длительность** сегмента — **от 10 до 300 секунд**; для этого в видео должна быть хотя бы
```

Заменить на:

```
## Определение и границы

<div class="keyfacts">
<div class="kf-stats">
<div class="kf-stat">
<div class="kf-value">10–300<span>сек</span></div>
<div class="kf-label">длительность одного сегмента</div>
</div>
</div>
<div class="kf-forbid">
<div class="kf-forbid-label">🚫 Сегмент не должен содержать</div>
<div class="kf-tags">
<span class="kf-tag">смену кадра</span>
<span class="kf-tag">склейки</span>
<span class="kf-tag">рамки</span>
<span class="kf-tag">водяные знаки</span>
<span class="kf-tag">наложенный текст</span>
</div>
</div>
</div>

- ⏱️ **Длительность** сегмента — **от 10 до 300 секунд**; для этого в видео должна быть хотя бы
```

- [ ] **Шаг 2: Карточка лимита сегментов — `manual-2-etap/02-segments.md`**

Текущий текст (сразу после заголовка «Ограничения интерфейса»):

```
## Ограничения интерфейса

- На одном видео можно выделить **максимум 10 сегментов** (слоты пронумерованы от 1 до 10,
```

Заменить на:

```
## Ограничения интерфейса

<div class="keyfacts">
<div class="kf-stats">
<div class="kf-stat">
<div class="kf-value">10<span>сегментов</span></div>
<div class="kf-label">максимум на одном видео</div>
</div>
</div>
</div>

- На одном видео можно выделить **максимум 10 сегментов** (слоты пронумерованы от 1 до 10,
```

- [ ] **Шаг 3: Карточка порогов экзамена/качества (2 этап) — `manual-2-etap/00b-exam.md`**

Текущий текст (весь файл начинается так):

```
# Экзамен и допуск

> Как оценивают асессора: входной экзамен на старте («Ступень 2») и отдельный, постоянно
> действующий порог качества уже работающей команды — это два разных порога, не путать один с
> другим.

## Обучение и входной экзамен «Ступень 2»
```

Заменить на:

```
# Экзамен и допуск

> Как оценивают асессора: входной экзамен на старте («Ступень 2») и отдельный, постоянно
> действующий порог качества уже работающей команды — это два разных порога, не путать один с
> другим.

<div class="keyfacts">
<div class="kf-stats">
<div class="kf-stat">
<div class="kf-value">≥80<span>%</span></div>
<div class="kf-label">порог входного экзамена</div>
</div>
<div class="kf-stat">
<div class="kf-value">85<span>%</span></div>
<div class="kf-label">текущий порог качества</div>
</div>
</div>
</div>

## Обучение и входной экзамен «Ступень 2»
```

- [ ] **Шаг 4: Карточка нормативов (3 этап) — `manual-3-etap/00-overview.md`**

Текущий текст (раздел «Нормативы»):

```
## Нормативы

- **Норматив времени на задание:** 250 секунд. Значительно более быстрое выполнение — сигнал
```

Заменить на:

```
## Нормативы

<div class="keyfacts">
<div class="kf-stats">
<div class="kf-stat">
<div class="kf-value">≥80<span>%</span></div>
<div class="kf-label">проходной балл экзамена</div>
</div>
<div class="kf-stat">
<div class="kf-value">95<span>%</span></div>
<div class="kf-label">текущий норматив качества</div>
</div>
</div>
</div>

- **Норматив времени на задание:** 250 секунд. Значительно более быстрое выполнение — сигнал
```

- [ ] **Шаг 5: Проверить заголовки/якоря всех 3 файлов не сдвинулись**

Run:
```bash
grep -n '^#' "manual-2-etap/02-segments.md"
grep -n '^#' "manual-2-etap/00b-exam.md"
grep -n '^#' "manual-3-etap/00-overview.md"
```
Expected: в каждом файле — тот же список заголовков и в том же порядке, что и до правки.

- [ ] **Шаг 6: Build-diff — сайт**

```bash
cd site
git stash
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict --config-file mkdocs.yml 2>&1 | tail -n 40 > /tmp/before-keyfacts.txt
git stash pop
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict --config-file mkdocs.yml 2>&1 | tail -n 40 > /tmp/after-keyfacts.txt
diff /tmp/before-keyfacts.txt /tmp/after-keyfacts.txt
```

Expected: оба билда — exit 0, `diff` не показывает новых `WARNING`-строк.

- [ ] **Шаг 7: Проверить, что все 4 карточки попали в собранный HTML сайта**

```bash
grep -o 'class="keyfacts"' "$(find "/d/ПРОЕКТЫ с Ai/avatar-manual-build/build/manual-2-etap/02-segments" -iname index.html)" | wc -l
grep -o 'class="keyfacts"' "$(find "/d/ПРОЕКТЫ с Ai/avatar-manual-build/build/manual-2-etap/00b-exam" -iname index.html)" | wc -l
grep -o 'class="keyfacts"' "$(find "/d/ПРОЕКТЫ с Ai/avatar-manual-build/build/manual-3-etap/00-overview" -iname index.html)" | wc -l
```

Expected: первая команда — `2` (обе карточки `02-segments.md`), вторая и третья — по `1`.

- [ ] **Шаг 8: Build-diff — PDF-профиль (карточки физически есть в HTML, но скрыты)**

```bash
cd site
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict --config-file mkdocs-pdf.yml 2>&1 | tail -n 40
grep -c 'class="keyfacts"' "$(find "/d/ПРОЕКТЫ с Ai/avatar-manual-build/build-pdf/manual-2-etap/02-segments" -iname index.html)"
```

Expected: build — exit 0, без новых WARNING; вторая команда — `2` (блоки физически в разметке,
скрыты только CSS-правилом из Task 1 Шаг 2, а не отсутствием в HTML).

- [ ] **Шаг 9: Финальный прогон тестов**

Run: `cd site/hooks && python -m pytest tests/ -q`
Expected: `125 passed` (без изменений — эта задача не добавляет и не ломает ни одного теста).

- [ ] **Шаг 10: Коммит**

```bash
git add manual-2-etap/02-segments.md manual-2-etap/00b-exam.md manual-3-etap/00-overview.md
git commit -m "4 карточки-факта (.keyfacts) в 02-segments.md ×2, 00b-exam.md, manual-3-etap/00-overview.md — визуальное выделение уже присутствующих в прозе чисел (Task 2, дизайн-документ 2026-08-12-fact-cards-design.md), без единой правки самого текста"
```

---

## Self-Review (выполнено при написании плана)

1. **Покрытие спеки:** все 4 карточки из дизайн-документа покрыты — карточка 1 (длительность +
   список «нельзя») и карточка 2 (лимит сегментов) в Task 2 Шаг 1-2, карточка 3 (2 этап) в
   Шаге 3, карточка 4 (3 этап) в Шаге 4. PDF-скрытие — Task 1 Шаг 2. Проверка — Task 2
   Шаги 5-9.
2. **Плейсхолдеры:** просканировано — нет TBD/TODO, весь HTML/CSS дан целиком, команды проверки
   — с точным ожидаемым выводом.
3. **Согласованность имён:** классы, объявленные в Task 1 (`.keyfacts`, `.kf-stats`, `.kf-stat`,
   `.kf-value`, `.kf-label`, `.kf-forbid`, `.kf-forbid-label`, `.kf-tags`, `.kf-tag`), — те же
   строки использованы во всех 4 HTML-блоках Task 2. Проверено построчным сравнением.

## Обоснование Inline Execution

Как и в двух предыдущих волнах того же дня (градиентная шкала/блок-схема, визуальная система
3 этапа), объём небольшой (CSS + 4 точечные вставки, без нового Python-кода) и контроллер уже
держит в контексте все нужные файлы и утверждённый макет-референс — дополнительный субагент не
добавил бы качества, только накладные расходы на повторное чтение того же контекста.

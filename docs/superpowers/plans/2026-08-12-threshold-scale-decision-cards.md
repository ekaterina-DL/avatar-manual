# Градиентная шкала и блок-схема «Сегмент/Битое» — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (Inline Execution — approved for this plan given its small size) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить в `manual-2-etap/02-segments.md` два визуальных блока-шкалы (молчание,
перекрытие рта) и один блок-схему («Сегмент или „Битое“?»), видимые только на сайте — без потери
ни одного слова существующего текста и без изменений в PDF-профиле.

**Architecture:** Прямые HTML-блоки (`<div>`) вставляются вручную прямо в markdown-источник —
никакого нового Python-хука. Рендерится через уже подключённое расширение `md_in_html`. Новый CSS
в `site/theme/extra.css` стилизует блоки на сайте; одно правило `display: none` в
`site/pdf/pdf-extra.css` скрывает их в PDF-профиле — там остаётся только уже присутствующий рядом
текст.

**Tech Stack:** mkdocs-material, Python-Markdown (`md_in_html`), чистый CSS (без препроцессоров).

## Global Constraints

- Ни один существующий символ текста в `02-segments.md` не удаляется и не переформулируется —
  блоки только добавляются после существующих абзацев/списков.
- Заголовки разделов не трогаются (якорная безопасность) — вставки идут строго внутри тела
  раздела, не задевая ни один `#`/`##`/`###`.
- `markdown="1"` не используется ни на одном новом `<div>` — содержимое блоков чисто текстовое
  (без **bold**/`[ссылок]`), по образцу уже существующего `.apeal-flow`
  (`site/hooks/build_dispute_flow.py`), где `markdown="1"` тоже не применяется.
- Цвета — только через существующие CSS-переменные (`--ok-color`, `--no-color`,
  `--md-accent-fg-color`, `--ok-bg`, `--no-bg`, `--gray-50/100/300/600`, `--card-line`,
  `--card-shadow`) — новых цветовых токенов не вводится.
- После каждой задачи: `cd site/hooks && python -m pytest tests/ -q` должен остаться зелёным без
  изменений (114 тестов) — эта работа не трогает ни один хук.
- Build-diff обоих профилей (`mkdocs.yml` и `mkdocs-pdf.yml`) через `python -m mkdocs build
  --strict` не должен добавлять новых WARNING-строк.

---

## Task 1: CSS для шкалы и карточек-исходов

**Files:**
- Modify: `site/theme/extra.css` (добавить в конец файла, после текущей последней строки 361)
- Modify: `site/pdf/pdf-extra.css` (добавить в конец файла, после текущей последней строки 29)

**Interfaces:**
- Produces (используется Task 2 в HTML-разметке `02-segments.md`): классы `.threshold-scale`,
  `.ts-caption`, `.ts-track` (принимает inline `style="background:linear-gradient(...)"` от
  вызывающего HTML), `.ts-tick`, `.ts-zone` — для градиентных шкал; классы `.decision-outcome`,
  `.do-question`, `.do-cards`, `.do-card` (+ модификаторы `.good`/`.bad`), `.do-tag`, `.do-body` —
  для блок-схемы.

- [ ] **Шаг 1: Дописать блок шкалы порогов в `site/theme/extra.css`**

Открыть файл, перейти в конец (после строки 361, `.example-card .ec-body ul, ... margin: .3em 0
0; }`), добавить:

```css

/* Градиентная шкала многоуровневых порогов (02-segments.md) — прямой HTML-блок в исходнике,
   без отдельного хука. См. addendum 12.08.2026 к
   docs/superpowers/specs/2026-08-11-stage2-dedup-design.md. Заливка трека (linear-gradient) —
   inline style в самом HTML-блоке каждой шкалы, т.к. точки остановки у шкал разные. */
.threshold-scale {
  margin: 1.4em 0;
  padding: 16px 18px 34px;
  border: 1px solid var(--card-line);
  border-radius: 10px;
  background: var(--gray-50);
  box-shadow: var(--card-shadow);
}
.threshold-scale .ts-caption {
  font-family: 'Golos Text', sans-serif;
  font-size: .72rem;
  font-weight: 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--gray-600);
  margin-bottom: 26px;
}
.threshold-scale .ts-track {
  position: relative;
  height: 8px;
  border-radius: 5px;
  margin: 0 8px;
}
.threshold-scale .ts-tick {
  position: absolute;
  top: -20px;
  transform: translateX(-50%);
  font-family: 'Golos Text', sans-serif;
  font-size: .72rem;
  color: var(--gray-600);
  white-space: nowrap;
}
.threshold-scale .ts-tick::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 18px;
  width: 1px;
  height: 8px;
  background: var(--gray-300);
}
.threshold-scale .ts-zone {
  position: absolute;
  top: 16px;
  transform: translateX(-50%);
  width: 110px;
  font-size: .72rem;
  color: var(--gray-600);
  text-align: center;
}
@media (max-width: 480px) {
  .threshold-scale .ts-caption { margin-bottom: 34px; }
  .threshold-scale .ts-zone { font-size: .66rem; width: 84px; }
}

/* Карточки-исходы блок-схемы «Сегмент или Битое?» (02-segments.md) — самостоятельный класс, не
   переиспользует .compare-card: тот показывается и в PDF (настоящие фотопримеры), а этот
   декоративный элемент в PDF, наоборот, скрывается (см. site/pdf/pdf-extra.css). */
.decision-outcome {
  margin: 1.4em 0;
}
.decision-outcome .do-question {
  font-size: .95rem;
  margin: 0 0 12px;
}
.decision-outcome .do-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
@media (max-width: 560px) {
  .decision-outcome .do-cards { grid-template-columns: 1fr; }
}
.decision-outcome .do-card {
  border-radius: 10px;
  border: 1px solid var(--card-line);
  background: var(--gray-50);
  box-shadow: var(--card-shadow);
  overflow: hidden;
}
.decision-outcome .do-card.good { border-color: var(--ok-color); }
.decision-outcome .do-card.bad { border-color: var(--no-color); }
.decision-outcome .do-tag {
  padding: 8px 12px;
  font-family: 'Golos Text', sans-serif;
  font-size: .82rem;
  font-weight: 700;
}
.decision-outcome .do-card.good .do-tag { background: var(--ok-bg); color: var(--ok-color); }
.decision-outcome .do-card.bad .do-tag { background: var(--no-bg); color: var(--no-color); }
.decision-outcome .do-body {
  padding: 10px 12px 13px;
  font-size: .85rem;
  color: var(--gray-600);
  line-height: 1.5;
}
```

- [ ] **Шаг 2: Дописать правило скрытия в `site/pdf/pdf-extra.css`**

Открыть файл, перейти в конец (после строки 29, `.video-grid { break-inside: avoid; }`),
добавить:

```css

/* Декоративные визуальные добавки (градиентная шкала, карточки-исходы «Сегмент/Битое») —
   только сайт; PDF показывает уже присутствующий рядом полный текст без изменений.
   См. addendum 12.08.2026 к docs/superpowers/specs/2026-08-11-stage2-dedup-design.md */
.threshold-scale,
.decision-outcome {
  display: none;
}
```

- [ ] **Шаг 3: Проверить, что тесты хуков не сломались**

Run: `cd site/hooks && python -m pytest tests/ -q`
Expected: `114 passed` (CSS-файлы не затрагивают Python-хуки — количество тестов не меняется).

- [ ] **Шаг 4: Закоммитить**

```bash
git add site/theme/extra.css site/pdf/pdf-extra.css
git commit -m "CSS для градиентной шкалы порогов и карточек-исходов «Сегмент/Битое» — контента,
который их использует, пока нет, стили подключены заранее (Task 2 addendum 12.08.2026)"
```

---

## Task 2: Вставка блоков в `manual-2-etap/02-segments.md`

**Files:**
- Modify: `manual-2-etap/02-segments.md:69-71` (после раздела «Определение и границы» — 2 блока
  шкал)
- Modify: `manual-2-etap/02-segments.md:165-167` (внутри раздела «Когда видео помечается «Битое»»
  — 1 блок карточек-исходов)

**Interfaces:**
- Consumes: классы из Task 1 — `.threshold-scale`/`.ts-caption`/`.ts-track`/`.ts-tick`/`.ts-zone`,
  `.decision-outcome`/`.do-question`/`.do-cards`/`.do-card`/`.do-tag`/`.do-body`.

- [ ] **Шаг 1: Вставить шкалу молчания и шкалу перекрытия рта**

Текущий текст (строки 67-71 файла `manual-2-etap/02-segments.md`):

```
  `[Разметка ВК видео — ОС Экзамен 18.05 / 28.05 СТ2; Памятка «Аватар 2 этап», стр.4]`

`[Инстр. Kandinsky-Аватар, стр.2, 10]`

## Ограничения интерфейса
```

Заменить на:

```
  `[Разметка ВК видео — ОС Экзамен 18.05 / 28.05 СТ2; Памятка «Аватар 2 этап», стр.4]`

`[Инстр. Kandinsky-Аватар, стр.2, 10]`

<div class="threshold-scale">
<div class="ts-caption">🔇 Молчание — допустимая длительность</div>
<div class="ts-track" style="background:linear-gradient(90deg,var(--ok-color) 0%,var(--ok-color) 35%,var(--md-accent-fg-color) 35%,var(--md-accent-fg-color) 62%,var(--ok-color) 62%,var(--ok-color) 78%,var(--no-color) 78%,var(--no-color) 100%)">
<span class="ts-tick" style="left:0%">0с</span>
<span class="ts-tick" style="left:35%">2с</span>
<span class="ts-tick" style="left:62%">3–5с</span>
<span class="ts-tick" style="left:78%">&gt;5с</span>
<span class="ts-zone" style="left:17%">ок везде</span>
<span class="ts-zone" style="left:48%">граница/внутри</span>
<span class="ts-zone" style="left:89%">резать</span>
</div>
</div>

<div class="threshold-scale">
<div class="ts-caption">🤐 Перекрытие рта — насколько критично</div>
<div class="ts-track" style="background:linear-gradient(90deg,var(--ok-color) 0%,var(--ok-color) 40%,var(--md-accent-fg-color) 40%,var(--md-accent-fg-color) 75%,var(--no-color) 75%,var(--no-color) 100%)">
<span class="ts-tick" style="left:0%">доля сек.</span>
<span class="ts-tick" style="left:40%">неск. сек.</span>
<span class="ts-tick" style="left:75%">&gt;50% сегмента</span>
<span class="ts-zone" style="left:20%">ок</span>
<span class="ts-zone" style="left:57%">обрезать участок</span>
<span class="ts-zone" style="left:90%">сегмент целиком не подходит</span>
</div>
</div>

## Ограничения интерфейса
```

- [ ] **Шаг 2: Вставить карточки-исходы «Сегмент или Битое?»**

Текущий текст (строки 163-167 файла, после правки Шага 1 номера строк сдвинутся — искать по
тексту, не по номеру):

```
«Битое» важно убедиться, что во всём видео действительно нет ни одного подходящего отрезка от
10 секунд — наличие одного «плохого» признака (например, где-то есть склейка) не значит, что
всё видео нужно браковать целиком. `[Памятка «Аватар 2 этап», стр.3]`

Это два взаимоисключающих варианта: **либо** выделяются сегменты, **либо** ставится «Битое» —
```

Заменить на:

```
«Битое» важно убедиться, что во всём видео действительно нет ни одного подходящего отрезка от
10 секунд — наличие одного «плохого» признака (например, где-то есть склейка) не значит, что
всё видео нужно браковать целиком. `[Памятка «Аватар 2 этап», стр.3]`

<div class="decision-outcome">
<div class="do-question">Есть ≥1 непрерывный участок 10+ сек без артефактов?</div>
<div class="do-cards">
<div class="do-card good">
<div class="do-tag">✅ Да → Сегмент</div>
<div class="do-body">Выделяем найденный участок</div>
</div>
<div class="do-card bad">
<div class="do-tag">🚫 Нет → Битое</div>
<div class="do-body">Только если во всём видео нет ни одного такого участка</div>
</div>
</div>
</div>

Это два взаимоисключающих варианта: **либо** выделяются сегменты, **либо** ставится «Битое» —
```

- [ ] **Шаг 3: Убедиться, что заголовки/якоря не сдвинулись**

Run: `grep -n '^#' "manual-2-etap/02-segments.md"`
Expected: тот же список заголовков и в том же порядке, что и до правки (12 заголовков, от `#
Сегменты` до `## Антипримеры`) — вставленные блоки не добавляют и не удаляют ни одного `#`.

- [ ] **Шаг 4: Build-diff — сайт**

```bash
cd site
git stash
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict --config-file mkdocs.yml 2>&1 | tail -n 30 > /tmp/before-site.txt
git stash pop
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict --config-file mkdocs.yml 2>&1 | tail -n 30 > /tmp/after-site.txt
diff /tmp/before-site.txt /tmp/after-site.txt
```

Expected: оба билда завершаются с exit 0 (strict-режим не падает на WARNING), `diff` не
показывает новых строк `WARNING` (допустимы уже существовавшие до правки INFO-уведомления про
якоря — они не относятся к этой правке).

- [ ] **Шаг 5: Проверить, что новые блоки реально попали в собранный HTML сайта**

```bash
grep -o 'class="threshold-scale"' site/build/manual-2-etap/02-segments/index.html | wc -l
grep -o 'class="decision-outcome"' site/build/manual-2-etap/02-segments/index.html | wc -l
```

Expected: первая команда — `2` (обе шкалы), вторая — `1` (карточки-исходы). Если 0 — `md_in_html`
не распознал блок как raw HTML (проверить отступы и пустые строки вокруг `<div>`).

- [ ] **Шаг 6: Build-diff — PDF-профиль**

```bash
cd site
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m mkdocs build --strict --config-file mkdocs-pdf.yml 2>&1 | tail -n 30
```

Expected: exit 0, без новых WARNING (тот же принцип, что в Шаге 4 — здесь достаточно свежего
билда без diff, т.к. PDF-профиль не менялся структурно, только унаследовал новые CSS-правила
скрытия из Task 1).

- [ ] **Шаг 7: Убедиться, что pytest всё ещё зелёный**

Run: `cd site/hooks && python -m pytest tests/ -q`
Expected: `114 passed`.

- [ ] **Шаг 8: Закоммитить**

```bash
git add manual-2-etap/02-segments.md
git commit -m "02-segments.md: градиентная шкала молчания и перекрытия рта + карточки-исходы
«Сегмент или Битое?» — визуальное дополнение поверх существующего текста (addendum 12.08.2026 к
2026-08-11-stage2-dedup-design.md), без единой правки самого текста"
```

---

## Self-Review (выполнено при написании плана)

1. **Покрытие спеки:** addendum описывает 2 шкалы (молчание, перекрытие рта) + 1 блок-схему
   («Сегмент/Битое») + CSS + PDF-скрытие — все 4 пункта покрыты Task 1 (CSS/PDF-правило) и
   Task 2 (контент). «Сколько сегментов» и «резать по молчанию или нет» осознанно исключены
   addendum'ом — задач под них нет, это соответствует спеке, а не пропуск.
2. **Плейсхолдеры:** просканировано — нет TBD/TODO, весь HTML/CSS дан целиком, команды проверки
   — с точным ожидаемым выводом.
3. **Согласованность имён:** классы, объявленные в Task 1 (`.threshold-scale`, `.ts-caption`,
   `.ts-track`, `.ts-tick`, `.ts-zone`, `.decision-outcome`, `.do-question`, `.do-cards`,
   `.do-card`, `.do-tag`, `.do-body`), — те же самые строки использованы в HTML Task 2, включая
   модификаторы `.good`/`.bad`. Проверено построчным сравнением.

## Что сознательно не входит в этот план

- Блок-схема «Сколько сегментов выделять» — решено addendum'ом не делать (см. дизайн-документ).
- Отдельная блок-схема «Резать по молчанию или нет» — дублировала бы шкалу молчания, не делаем.
- Мобильная адаптация сверх заложенных `@media`-правил (480px для шкал, 560px для карточек) —
  повторяет уже существующие в файле брейкпоинты (`.example-grid`, `.compare`), отдельного
  тестирования вне объёма этого плана.

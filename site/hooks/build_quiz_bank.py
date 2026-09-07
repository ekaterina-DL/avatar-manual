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
from _section_utils import extract_section

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
        # Число 10:15 живёт на 05b-what-not-to-label.md (раздел «Другие исключения»),
        # а не на 02-segments.md — 02-segments.md его не содержит.
        "page": "manual-2-etap/05b-what-not-to-label.md",
        "confirm": r"10:15",
        "question": "Какова максимальная длина исходного видео, которое ещё берём в работу?",
        "correct": "10:15",
        "wrong": ["10:00", "9:30", "15:00"],
        "anchor": "другие-исключения",
        "title": "Что не размечаем",
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


# Маркеры отрицания/смягчения в подписи примера: если подпись их содержит, пример —
# контрпример («так делать НЕ надо считать браком»), в вопрос он не идёт.
# Значок «✅» в подписи мануала помечает «этот пример — годный, не брак» (напр.
# «✅ Умеренная тряска — сегмент годен» в разделе «Тряска камеры»); подписи с «❌»
# при этом остаются — это как раз примеры дефекта.
_NEGATION_MARKERS = ("нет ", "некритичн", "для сравнения", "допустим", "не всегда",
                     "баг плеер", "✅")
_LINK_ITEM_RE = re.compile(r'^\s*[-*]\s+\[(?P<cap>[^\]]+)\]\((?P<url>[^)]+)\)', re.M)
_EXCLUDED_SUBHEAD_RE = re.compile(
    r'^###\s+(?P<name>.+?)\s+\{:\s*\.field-label-heading\s*\}\s*$', re.M
)

# Запасной пул категорий-дистракторов для вопроса «что не так с этим видео»: если у
# подраздела нашлось меньше трёх соседних заголовков (вырожденный раздел), варианты
# добираются отсюда, чтобы у вопроса всегда было >= 3 варианта. Верный ответ при этом
# всегда берётся из заголовка самого мануала — здесь только неверные.
_EXCLUDED_TYPE_DISTRACTORS = (
    "Склейки", "Рамка", "Пиксельность", "Тряска камеры", "Пережатие",
    "Виньетка", "Монтажное наложение", "Дубляж", "Синхронизация", "Смена кадра/сцены",
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
    if len(heads) < 2:
        return []
    names = [h.group("name").strip() for h in heads]
    out = []
    for i, h in enumerate(heads):
        name = names[i]
        seg_start = h.end()
        seg_end = heads[i + 1].start() if i + 1 < len(heads) else len(body)
        segment = body[seg_start:seg_end]
        others = [n for n in names if n != name][:3]
        if len(others) < 3:  # вырожденный раздел — добираем неверные из запасного пула
            for d in _EXCLUDED_TYPE_DISTRACTORS:
                if d != name and d not in others:
                    others.append(d)
                if len(others) >= 3:
                    break
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


def build_bank(sources, manual_yaml_text):
    """sources: {relpath: markdown_text}. Возвращает {"generatedAt": iso, "questions": [...]}.
    Экстракторы источников A–F подключаются в Задачах 3–8."""
    questions = []
    questions += extract_numbers(sources)
    questions += extract_forbidden_tags(sources)
    questions += extract_classifier_video(sources)
    questions += extract_broken(sources)
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

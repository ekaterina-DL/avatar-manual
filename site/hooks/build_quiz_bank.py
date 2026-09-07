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


def build_bank(sources, manual_yaml_text):
    """sources: {relpath: markdown_text}. Возвращает {"generatedAt": iso, "questions": [...]}.
    Экстракторы источников A–F подключаются в Задачах 3–8."""
    questions = []
    questions += extract_numbers(sources)
    questions += extract_forbidden_tags(sources)
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

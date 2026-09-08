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
import random
import re
from pathlib import Path

import yaml

from pymdownx.slugs import slugify as _slugify_factory

from _build_profile import is_pdf_build
from _section_utils import extract_section

TARGET_PAGE = "manual-2-etap/07-testirovanie.md"

# Настоящий slug-генератор mkdocs (pymdownx.slugs.slugify(case=lower)) — тот же, что в
# site/mkdocs.yml. Используем его везде, где нужно собрать якорь заголовка (#...), чтобы
# ссылка review.url гарантированно вела в нужную секцию, а не «примерно туда».
_heading_slug = _slugify_factory(case="lower")

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


# Транслитерация кириллицы для id вопросов. Без неё _slug() любого чисто-кириллического
# topic'а схлопывался в "q", и id разных тем сталкивались бы (напр. A-q-<hash> для
# «Освещение» и «Фон» при одном и том же url), а проигравший вопрос молча выкидывался
# дедупом. Транслит + хэш содержимого делают id по-настоящему уникальным.
_RU2LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def _translit(text):
    return "".join(_RU2LAT.get(ch, ch) for ch in text)


def _slug(text):
    """ASCII-безопасный короткий слаг для id: сначала нижний регистр, потом транслит
    кириллицы в латиницу, потом чистка до [a-z0-9-]."""
    text = _translit(text.lower())
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
    # Дистракторы тасуем с фиксированным seed'ом: детерминированно на сборку, но не
    # «первые три из списка» — иначе набор неверных был бы всегда один и тот же.
    pool = list(_ALLOWED_DISTRACTORS)
    random.Random("forbidden-tags").shuffle(pool)
    wrong = pool[:3]
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

_MEDIA_HINTS = ("vkvideo.ru", "vk.com/video", "youtube.com", "youtu.be")


def _looks_like_media(url):
    """True, если ссылка похожа на видео-источник, а не на внутреннюю страницу мануала.
    Защищает от того, чтобы пункт вида «- [см. Общие требования](01-general-requirements.md)»
    превратился в вопрос про «битое» видео."""
    if not url:
        return False
    u = url.strip().lower()
    if u.startswith(("http://", "https://")):
        return True
    if u.endswith((".mp4", ".webm", ".mov")):
        return True
    return any(h in u for h in _MEDIA_HINTS)


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
    # Якорь заголовка вида "### 3. Объём и поза…" — считаем настоящим slug'ом mkdocs,
    # а не ручной эмуляцией (её легко рассинхронить с pymdownx).
    return _heading_slug(f"{index_word} {field_name}", "-")


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
            if not _looks_like_media(url):
                continue
            rest = ex.group("rest") or ""
            start = _parse_timecode(rest)
            wrong = [v for v in values if v != canon]
            # Тасуем дистракторы с per-question seed'ом (url): детерминированно на сборку,
            # но набор неверных вариантов разный от вопроса к вопросу, а не «первые три».
            random.Random(url).shuffle(wrong)
            distractors = wrong[:3]
            idx_word = idx_by_name.get(field_name, "")
            q = {
                "id": _make_id("A", field_name, url),
                "category": "A",
                "topic": field_name,
                "question": f"Определите по видео: {field_name.lower()}.",
                "videoUrl": url,
                "videoKind": _video_kind(url),
                "options": [canon, *distractors],
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

def _clean_caption(cap):
    cap = re.sub(r'\*\*(.+?)\*\*', r'\1', cap)  # снять bold
    return cap.strip().rstrip(".").strip()


def _has_negation(cap):
    low = cap.lower()
    return any(mk in low for mk in _NEGATION_MARKERS)


# Источник B-1: раздел «Битое — примеры дефектов» в 11-example-library.md.
# Раньше вопрос был «Какой дефект в этом видео?» с соседними подписями-дистракторами —
# он неотвечаем, когда подписи-синонимы («Размазаны глаза» / «Плохое качество с
# пиксельностью» / «Размазано лицо» — про одно и то же). Переформулировано в
# «размечать или в „Битое“?»: все видео в этом разделе действительно битые.
_BROKEN_LIB_OPTIONS = ["В «Битое»", "Подходит для разметки", "Нужно поделить на 2 сегмента"]


def _extract_broken_from_library(text):
    body = extract_section(text, "Битое — примеры дефектов")
    if body is None:
        return []
    out = []
    seen = set()
    for m in _LINK_ITEM_RE.finditer(body):
        cap = _clean_caption(m.group("cap"))
        url = m.group("url").strip()
        if not _looks_like_media(url) or url in seen:
            continue
        low = cap.lower()
        if "для сравнения" in low or "некритич" in low:
            continue  # лёгкая защита: таких пунктов в разделе сейчас нет
        seen.add(url)
        out.append({
            "id": _make_id("B", "битое дефект", url),
            "category": "B",
            "topic": "Что не размечаем / Битое",
            "question": "Это видео можно размечать или его нужно отправить в «Битое»?",
            "videoUrl": url,
            "videoKind": _video_kind(url),
            "options": list(_BROKEN_LIB_OPTIONS),
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
        # Граница подраздела — до ближайшего следующего «### » ЛЮБОГО вида (в т.ч.
        # не-field-label «### Другие исключения»), иначе последний подраздел затягивал
        # бы в себя чужой заголовок и его пункты.
        nxt = body.find("\n### ", seg_start)
        seg_end = nxt if nxt != -1 else len(body)
        segment = body[seg_start:seg_end]

        others = [n for n in names if n != name]
        if len(others) < 2:  # <2 соседних заголовков — не набрать >=3 варианта, пропускаем
            continue

        for m in _LINK_ITEM_RE.finditer(segment):
            cap = _clean_caption(m.group("cap"))
            url = m.group("url").strip()
            if not _looks_like_media(url):
                continue
            if not cap or _has_negation(cap):
                continue
            # Дистракторы тасуем с per-question seed'ом (url): без этого каждый подраздел
            # после первых трёх получал бы один и тот же набор вариантов.
            pool = list(others)
            random.Random(url).shuffle(pool)
            distractors = pool[:3]
            out.append({
                "id": _make_id("B", name, url),
                "category": "B",
                "topic": name,
                "question": "Что не так с этим видео — почему его нельзя размечать?",
                "videoUrl": url,
                "videoKind": _video_kind(url),
                "options": [name, *distractors],
                "answer": 0,
                "review": {"title": name,
                           "url": f"05b-what-not-to-label.md#{_heading_slug(name, '-')}"},
            })
    return out


def extract_broken(sources):
    out = []
    out += _extract_broken_from_library(sources.get("manual-2-etap/11-example-library.md", ""))
    out += _extract_broken_from_excluded(sources.get("manual-2-etap/05b-what-not-to-label.md", ""))
    return out


# Источник C: блоки «**Пример N:** …» из позитивного раздела и «**Антипример N:** …»
# из раздела антипримеров. URL — либо голой ссылкой, либо как [текст](url). Строка-кадр
# «![подпись](…jpeg)» под блоком в регэксп не попадает: у неё нет ведущих «**».
_EXAMPLE_BLOCK_RE = re.compile(
    r'\*\*(?P<kind>Анти)?[Пп]ример (?P<n>\d+):\*\*[ \t]*'
    r'(?:\[(?P<txt>[^\]]*)\]\((?P<lurl>[^)]+)\)|(?P<burl>\S+))',
    re.M,
)
_C_FIT = "Подходит для разметки"
_C_BROKEN = "В «Битое»"
_C_OPTIONS = [_C_FIT, _C_BROKEN]

# Вариант «Нужно поделить на N сегментов» здесь не используем: вопрос бинарный
# («подходит или в „Битое“?»), а комментарий мануала к «Примеру» относится к сегменту
# внутри видео, а не к видео целиком — многосегментное позитивное видео всё равно «подходит».


def _extract_examples_from(body, is_anti, review):
    if body is None:
        return []
    out = []
    for m in _EXAMPLE_BLOCK_RE.finditer(body):
        url = (m.group("lurl") or m.group("burl") or "").strip()
        if not url or url.startswith("!") or not _looks_like_media(url):
            continue
        correct = _C_BROKEN if is_anti else _C_FIT
        wrong = [o for o in _C_OPTIONS if o != correct]
        out.append({
            "id": _make_id("C", "подходящий сегмент", url),
            "category": "C",
            "topic": "Что размечаем",
            "question": "Это видео — подходящий сегмент или его нужно отправить в «Битое»?",
            "videoUrl": url,
            "videoKind": _video_kind(url),
            "options": [correct, *wrong],
            "answer": 0,
            "review": review,
        })
    return out


def extract_examples(sources):
    out = []
    pos = sources.get("manual-2-etap/05-what-to-label.md", "")
    if pos:
        out += _extract_examples_from(
            extract_section(pos, "Примеры (позитивные)"),
            is_anti=False,
            review={"title": "Что размечаем", "url": "05-what-to-label.md#примеры-позитивные"},
        )
    anti = sources.get("manual-2-etap/05b-what-not-to-label.md", "")
    if anti:
        out += _extract_examples_from(
            extract_section(anti, "Антипримеры"),
            is_anti=True,
            review={"title": "Что не размечаем / Битое",
                    "url": "05b-what-not-to-label.md#антипримеры"},
        )
    return out


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
        if len(set(map(str, opts))) != len(opts):
            raise ValueError(f"{where}: варианты ответа повторяются дословно")
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


def _fix_local_video_url(url):
    """Локальные видео в мануале ссылаются как `assets/...` — относительно папки страницы-
    источника (`manual-2-etap/`). Страница теста собирается на уровень глубже
    (`manual-2-etap/07-testirovanie/index.html`, use_directory_urls), поэтому из неё тот же
    файл — это `../assets/...`. Абсолютные (http/https/протокол-относительные `//`) и уже
    корневые (`/`) URL не трогаем. MkDocs не переписывает ссылки внутри <script>-банка и в
    DOM, который строит quiz.js, — поэтому правим здесь, на сборке банка."""
    if url.startswith(("http://", "https://", "//", "/", "../")):
        return url
    return "../" + url


def _fix_local_video_urls(questions):
    for q in questions:
        if q.get("videoUrl"):
            q["videoUrl"] = _fix_local_video_url(q["videoUrl"])


def build_bank(sources, manual_yaml_text):
    """sources: {relpath: markdown_text}. Возвращает {"generatedAt": iso, "questions": [...]}.
    Экстракторы источников A–F подключаются в Задачах 3–8."""
    questions = []
    questions += extract_numbers(sources)
    questions += extract_forbidden_tags(sources)
    questions += extract_classifier_video(sources)
    questions += extract_broken(sources)
    questions += extract_examples(sources)
    questions += load_manual_questions(manual_yaml_text)
    _assert_unique_ids(questions)
    _dedup_by_id(questions)  # защитный no-op: после _assert_unique_ids дублей уже нет
    _fix_local_video_urls(questions)
    return {
        "generatedAt": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "questions": questions,
    }


def _assert_unique_ids(questions):
    """Падаем со списком id, если два вопроса делят один id. После транслита _slug() и
    хэша по содержимому/URL реальный дубль id — это уже настоящая ошибка (в т.ч.
    задублированный вручную id в _quiz-manual.yml), а не безобидное совпадение слага."""
    seen = {}
    for q in questions:
        if q["id"] in seen:
            raise ValueError(
                f"дублирующийся id вопроса: {q['id']!r} "
                f"(темы: {seen[q['id']]!r} и {q['topic']!r})"
            )
        seen[q["id"]] = q["topic"]


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

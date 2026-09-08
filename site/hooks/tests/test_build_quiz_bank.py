import json
import re

from build_quiz_bank import on_page_markdown, build_bank, TARGET_PAGE, SOURCE_FILES
from build_quiz_bank import extract_numbers, extract_forbidden_tags
from build_quiz_bank import extract_classifier_video

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
    from build_quiz_bank import _ALLOWED_DISTRACTORS
    qs = extract_forbidden_tags({"manual-2-etap/02-segments.md": SEGMENTS_KEYFACTS})
    assert qs
    q = qs[0]
    assert q["category"] == "DE"
    assert len(q["options"]) >= 3
    # верный вариант — один из запрещённых тегов
    assert q["options"][0] in {"смену кадра", "склейки", "закадровый голос",
                               "молчание >4 сек и на границах"} or "молчание" in q["options"][0]
    # неверные варианты — ровно 3 «допустимые» вещи из общего пула (порядок тасуется seed'ом)
    distractors = q["options"][1:]
    assert len(distractors) == 3
    assert all(d in _ALLOWED_DISTRACTORS for d in distractors)


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
- [**Стоя в полный рост** — колени уже видны](https://ex.test/notc.mp4)

### 4. Преобладающий ракурс

<ul class="value-checklist">
<li>Анфас</li>
<li>Полуоборот (3/4)</li>
<li>Профиль</li>
</ul>

**Примеры:**

- [**Анфас** (0:06.48–0:18.06)](https://ex.test/c.mp4)
- [**Профиль**](https://ex.test/ak/avatar/zzz/trimmed/-1_2__segment_1_0_50.mp4)
- [**Ракурс меняется в пределах ролика** — берём преобладающее](https://ex.test/d.mp4)
"""


def _by_url(qs, url):
    return next(q for q in qs if q["videoUrl"] == url)


def test_extract_classifier_video_basic():
    qs = extract_classifier_video({"manual-2-etap/04-classifier.md": CLASSIFIER_A})
    q = _by_url(qs, "https://ex.test/a.mp4")
    assert q["category"] == "A"
    assert q["topic"] == "Объём и поза тела человека в кадре"
    assert q["videoKind"] == "mp4"
    assert q["videoStart"] == 78.4
    assert q["videoEnd"] == 95.9
    # тайм-код сегмента виден прямо в тексте вопроса
    assert q["question"] == (
        "Определите по видео: объём и поза тела человека в кадре. "
        "Оцениваемый сегмент: 1:18–1:36."
    )
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
    # "Ракурс меняется…" не совпал со значением чек-листа -> вопроса нет
    assert not [q for q in qs if q["videoUrl"] == "https://ex.test/d.mp4"]


def test_extract_classifier_video_timecode_mm_ss():
    qs = extract_classifier_video({"manual-2-etap/04-classifier.md": CLASSIFIER_A})
    anfas = _by_url(qs, "https://ex.test/c.mp4")  # 0:06.48–0:18.06
    assert abs(anfas["videoStart"] - 6.48) < 0.001
    assert abs(anfas["videoEnd"] - 18.06) < 0.001
    assert "Оцениваемый сегмент: 0:06–0:18." in anfas["question"]


def test_extract_classifier_video_skips_untimed_full_source():
    # Полный видео-источник без тайм-кода в подписи — непонятно, какой момент оценивать
    qs = extract_classifier_video({"manual-2-etap/04-classifier.md": CLASSIFIER_A})
    assert not [q for q in qs if q["videoUrl"] == "https://ex.test/notc.mp4"]


def test_extract_classifier_video_trimmed_is_whole_clip():
    # Обрезанный ролик (/trimmed/…__segment_…) — это и есть один сегмент целиком
    qs = extract_classifier_video({"manual-2-etap/04-classifier.md": CLASSIFIER_A})
    q = _by_url(qs, "https://ex.test/ak/avatar/zzz/trimmed/-1_2__segment_1_0_50.mp4")
    assert q["question"].endswith("Оцениваемый сегмент — весь ролик.")
    assert "videoStart" not in q
    assert "videoEnd" not in q


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

## 🚫 Полностью исключённые дефекты

<div class="field-label-row" markdown="1">

### Склейки {: .field-label-heading }

Склейка внутри сегмента — брак.

</div>

**Калибровочные примеры:**

- [В начале склейка с наложением](https://ex.test/skl1.mp4).
- [3 склейки подряд](https://ex.test/skl2.mp4).

<div class="field-label-row" markdown="1">

### Виньетка {: .field-label-heading }

Затемнение по краям кадра.

</div>

**Калибровочный пример:**

- [Виньетка по углам кадра](https://ex.test/vin1.mp4).

<div class="field-label-row" markdown="1">

### Пиксельность {: .field-label-heading }

Черты лица смазаны.

</div>

**Калибровочные примеры пиксельности:**

- [Нет пиксельности, для сравнения](https://ex.test/px0.mp4).
- [Некритичная пиксельность (из-за освещения)](https://ex.test/px1.mp4).
- [Пиксельность — пример 2](https://ex.test/px2.mp4).
"""

EXCLUDED_WITH_OTHER_HEADING = """# Что не размечаем / Битое

## 🚫 Полностью исключённые дефекты

<div class="field-label-row" markdown="1">

### Склейки {: .field-label-heading }

Склейка — брак.

</div>

- [В начале склейка](https://ex.test/skl1.mp4).

<div class="field-label-row" markdown="1">

### Виньетка {: .field-label-heading }

Затемнение по краям.

</div>

- [Виньетка по углам](https://ex.test/vin1.mp4).

<div class="field-label-row" markdown="1">

### Пиксельность {: .field-label-heading }

Смазаны черты лица.

</div>

- [Пиксельность — пример](https://ex.test/px9.mp4).

### Другие исключения

- [см. Общие требования](https://ex.test/other.mp4)
"""

EXCLUDED_WITH_DOC_LINK = """# Что не размечаем / Битое

## 🚫 Полностью исключённые дефекты

<div class="field-label-row" markdown="1">

### Склейки {: .field-label-heading }

Склейка — брак.

</div>

- [В начале склейка](https://ex.test/skl1.mp4).
- [см. Общие требования](01-general-requirements.md).

<div class="field-label-row" markdown="1">

### Виньетка {: .field-label-heading }

Затемнение.

</div>

- [Виньетка](https://ex.test/vin1.mp4).

<div class="field-label-row" markdown="1">

### Пиксельность {: .field-label-heading }

Смазано.

</div>

- [Пиксельность](https://ex.test/px1.mp4).
"""


def test_extract_broken_from_example_library():
    qs = extract_broken({"manual-2-etap/11-example-library.md": LIB_BROKEN})
    lib = [q for q in qs if q["review"]["url"].startswith("11-example-library.md")]
    assert len(lib) == 4
    q = lib[0]
    assert q["category"] == "B"
    assert q["videoUrl"] == "https://ex.test/s1.mp4"
    # переформулировано: «размечать или в „Битое“?», верный ответ всегда «В «Битое»»
    assert q["options"][0] == "В «Битое»"
    assert q["answer"] == 0
    assert set(q["options"]) == {"В «Битое»", "Подходит для разметки", "Нужно поделить на 2 сегмента"}
    # одна карточка на ссылку
    assert len({x["videoUrl"] for x in lib}) == 4
    assert {x["videoUrl"] for x in lib} == {
        "https://ex.test/s1.mp4", "https://ex.test/s2.mp4",
        "https://ex.test/s3.mp4", "https://ex.test/s4.mp4",
    }


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
    assert q["topic"] == "Склейки"                       # topic = имя подраздела
    assert q["review"]["url"] == "05b-what-not-to-label.md#склейки"
    assert len(q["options"]) >= 3
    assert set(q["options"]) - {"Склейки"} <= {"Виньетка", "Пиксельность"}


def test_extract_broken_excluded_ignores_other_headings():
    # Последний field-label подраздел не должен затягивать «### Другие исключения»
    qs = extract_broken({"manual-2-etap/05b-what-not-to-label.md": EXCLUDED_WITH_OTHER_HEADING})
    urls = {q["videoUrl"] for q in qs}
    assert "https://ex.test/px9.mp4" in urls        # последний field-label подраздел работает
    assert "https://ex.test/other.mp4" not in urls  # пункт из «Другие исключения» не попал


def test_media_url_filter():
    # Пункт-ссылка на страницу мануала (не видео) не должен становиться вопросом
    qs = extract_broken({"manual-2-etap/05b-what-not-to-label.md": EXCLUDED_WITH_DOC_LINK})
    urls = {q["videoUrl"] for q in qs}
    assert "https://ex.test/skl1.mp4" in urls
    assert not any(u.endswith("01-general-requirements.md") for u in urls)


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

NOT_LABEL_ANTI = """# Что не размечаем / Битое

## Антипримеры

**Антипример 1:** https://www.youtube.com/shorts/kLTpStNQRF0
![Антипример 1: вертикальное видео, внизу наложен текст-субтитр](assets/antiexample1-frame.jpeg)
Не должно быть наложенного текста.

**Антипример 3:** [Антипример 3](assets/Memorable%20Monologue.mp4)
![Антипример 3: ведущая ток-шоу, в углу логотип-водяной знак](assets/antiexample3-frame.jpeg)
Водяной знак в кадре.

`[Инстр. Kandinsky-Аватар, стр.7-10]`
"""


def test_extract_examples_positive():
    qs = extract_examples({"manual-2-etap/05-what-to-label.md": WHAT_TO_LABEL_C})
    pos = [q for q in qs if q["review"]["url"] == "05-what-to-label.md#примеры-позитивные"]
    assert len(pos) == 2
    q = pos[0]
    assert q["category"] == "C"
    assert q["videoUrl"] == "https://vkvideo.ru/video712360465_456239217"
    assert q["videoKind"] == "vk"
    assert q["options"][0] == "Подходит для разметки"
    assert q["answer"] == 0
    assert q["options"] == ["Подходит для разметки", "В «Битое»"]  # бинарный вопрос, 2 варианта


def test_extract_examples_local_mp4_kind():
    qs = extract_examples({"manual-2-etap/05-what-to-label.md": WHAT_TO_LABEL_C})
    p4 = [q for q in qs if q["videoUrl"].endswith(".mp4")][0]
    assert p4["videoKind"] == "mp4"


def test_extract_examples_antipatterns_are_broken():
    qs = extract_examples({"manual-2-etap/05b-what-not-to-label.md": NOT_LABEL_ANTI})
    anti = [q for q in qs if q["review"]["url"] == "05b-what-not-to-label.md#антипримеры"]
    assert len(anti) == 2
    q = anti[0]
    assert q["category"] == "C"
    assert q["options"][0] == "В «Битое»"
    assert q["answer"] == 0
    assert q["videoKind"] in {"youtube", "mp4"}
    assert q["options"] == ["В «Битое»", "Подходит для разметки"]  # бинарный вопрос, 2 варианта


def test_extract_examples_combined():
    qs = extract_examples({
        "manual-2-etap/05-what-to-label.md": WHAT_TO_LABEL_C,
        "manual-2-etap/05b-what-not-to-label.md": NOT_LABEL_ANTI,
    })
    assert len(qs) == 4
    corrects = sorted(q["options"][0] for q in qs)
    assert corrects == ["В «Битое»", "В «Битое»", "Подходит для разметки", "Подходит для разметки"]


MULTI_SEG_C = """# Что размечаем

## Примеры (позитивные)

**Пример 1:** https://ex.test/one.mp4
![Пример 1: женщина на нейтральном фоне](assets/f1.jpeg)
Речь на нейтральном фоне — лицо чётко видно. **Подходящий сегмент: 0:02 – 02:57.**

**Пример 2:** https://ex.test/two.mp4
![Пример 2: девушка поёт у пианино](assets/f2.jpeg)
Отрывок с пением дома — лицо чётко видно.
**Подходящие сегменты:**
- сегмент с плечами: 0:08 – 0:37
- сегмент с появлением рук: 0:37 – 02:40
"""


def test_extract_examples_multi_segment_still_fits():
    # Многосегментное позитивное видео («Подходящие сегменты:» + список) — всё равно
    # «Подходит для разметки»: комментарий мануала про сегмент, а не про видео целиком.
    qs = extract_examples({"manual-2-etap/05-what-to-label.md": MULTI_SEG_C})
    pos = [q for q in qs if q["review"]["url"] == "05-what-to-label.md#примеры-позитивные"]
    assert len(pos) == 2
    for q in pos:
        assert q["options"] == ["Подходит для разметки", "В «Битое»"]
        assert q["answer"] == 0


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


def test_load_manual_questions_rejects_duplicate_options():
    y = '''
- id: x
  topic: T
  question: Q?
  options: [верно, дубль, дубль]
  answer: 0
  review: {title: T, url: 02-segments.md#определение-и-границы}
'''
    try:
        load_manual_questions(y)
        assert False, "ожидался ValueError"
    except ValueError as e:
        assert "повтор" in str(e).lower()


def test_load_manual_questions_empty():
    assert load_manual_questions("") == []
    assert load_manual_questions("[]") == []


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
        # C — бинарный вопрос «подходит / в „Битое“», ровно 2 варианта; остальные ≥ 3.
        assert len(q["options"]) >= (2 if q["category"] == "C" else 3), q
        assert q["answer"] == 0
        assert q["question"].strip()
        assert q["topic"].strip()
        assert q["review"]["url"]
        if "videoUrl" in q:
            assert q["videoKind"] in {"mp4", "vk", "youtube"}


def test_real_bank_review_anchors_exist():
    # Сверяем якорь review.url со слагами заголовков целевого файла. slugify — тот же,
    # что в site/mkdocs.yml (pymdownx.slugs.slugify(case=lower)). Дедуп-суффиксы (_1, _2)
    # не воспроизводим: в этих файлах повторов заголовков нет, а ручная эмуляция дедупа
    # хрупка — при реальном совпадении разбираем точечно.
    from pymdownx.slugs import slugify
    slug = slugify(case="lower")
    heading_re = re.compile(r'^#{1,6}\s+(.*?)\s*(?:\{:[^}]*\})?\s*$', re.M)

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
            cache[fname] = {
                slug(re.sub(r'<[^>]+>', '', m.group(1)), "-")
                for m in heading_re.finditer(text)
            }
        assert anchor in cache[fname], (
            f"{ref}: якоря '{anchor}' нет среди {sorted(cache[fname])[:20]}"
        )


from build_quiz_bank import _fix_local_video_url


def test_fix_local_video_url_prefixes_relative_assets():
    # `assets/x.mp4` в исходнике — относительно manual-2-etap/; со страницы теста
    # (manual-2-etap/07-testirovanie/) тот же файл — это ../assets/x.mp4
    assert _fix_local_video_url("assets/x.mp4") == "../assets/x.mp4"
    assert _fix_local_video_url("assets/Some%20Name.mp4") == "../assets/Some%20Name.mp4"


def test_fix_local_video_url_leaves_absolute_untouched():
    for u in (
        "https://vkvideo.ru/video1_2",
        "http://example.test/a.mp4",
        "//cdn.test/a.mp4",
        "/manual-2-etap/assets/a.mp4",
        "../assets/already.mp4",
    ):
        assert _fix_local_video_url(u) == u


def test_real_bank_local_video_urls_are_page_relative():
    bank = build_bank(_real_sources(), _real_manual_yaml())
    for q in bank["questions"]:
        u = q.get("videoUrl")
        if not u:
            continue
        if u.startswith(("http://", "https://", "//")):
            continue
        assert u.startswith("../assets/"), f"{q['id']}: локальный videoUrl не относителен странице теста: {u}"


from build_quiz_bank import _slug, _make_id, _assert_unique_ids


def test_slug_transliterates():
    # чисто-кириллические темы больше не схлопываются в "q" и не совпадают между собой
    assert _slug("Освещение") != _slug("Фон")
    assert _slug("Освещение") != "q"
    assert _slug("Фон") != "q"
    assert _slug("Освещение") == "osveschenie"
    assert re.fullmatch(r"[a-z0-9-]+", _slug("Смена кадра/сцены"))


def test_make_id_distinct_for_topics():
    assert _make_id("A", "Освещение", "u") != _make_id("A", "Фон", "u")


def test_assert_unique_ids_raises_on_collision():
    dup = [
        {"id": "X-1", "topic": "A"},
        {"id": "X-1", "topic": "B"},
    ]
    try:
        _assert_unique_ids(dup)
        assert False, "ожидался ValueError"
    except ValueError as e:
        assert "X-1" in str(e)


def test_real_bank_assert_unique_ids_passes():
    # build_bank сам вызывает _assert_unique_ids; здесь фиксируем, что на живом мануале он не падает
    build_bank(_real_sources(), _real_manual_yaml())

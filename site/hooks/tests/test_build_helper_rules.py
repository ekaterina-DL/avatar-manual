import json
import re
from pathlib import Path

import pytest
from mkdocs.exceptions import PluginError

from build_helper_rules import (BASE_URL, build_rules, load_rules_map, on_post_build,
                                read_version, section_to_text)

REPO = Path(__file__).resolve().parents[3]

PAGE = (
    "# Что не размечаем\n\n"
    "Вступление.\n\n"
    "- **Максимальная длина исходного видео — 20 минут**.\n\n"
    "`[Инструкция заказчика, 25.09.2026]`\n\n"
    "## Дефекты\n\n"
    "<div class=\"field-label-row\" markdown=\"1\">\n\n"
    "### Рамка {: .field-label-heading }\n\n"
    "Видео с рамками.\n\n"
    "</div>\n\n"
    "**Рамка по краям видео не всегда означает брак** — тонкая граница\n"
    "по краю кадра.\n\n"
    "- [Рамка справа](https://x/a.mp4)\n"
    "- [Статья](https://x/page.html)\n"
    "- [Локальный пример](assets/b.mp4)\n"
    "- ![grid: Картинка](assets/c.jpeg)\n\n"
    "### Другое\n\n"
    "- Видео с **изображениями, сгенерированными ИИ**.\n"
    "- **Замедленное или ускоренное видео** — недопустимо. Пример: [ускорение](assets/s.mp4).\n"
    "  `[Инструкция заказчика, 04.09.2026]`\n"
)

MAP = {
    "frame_border": {"page": "manual-2-etap/05b.md", "heading": "Рамка", "title": "Рамка"},
    "speed_change": {"page": "manual-2-etap/05b.md", "heading": "Другое", "title": "Скорость",
                     "contains": "ускоренное"},
    "duration_limit": {"page": "manual-2-etap/05b.md", "heading": "Что не размечаем",
                       "title": "Длина", "contains": "длина исходного видео"},
}


class FakeSiteDir:
    def __init__(self, value):
        self._value = str(value)

    def __str__(self):
        return self._value


class FakeConfig(dict):
    def __init__(self, docs_dir, site_dir):
        super().__init__(docs_dir=str(docs_dir), site_dir=str(site_dir))
        self.site_dir = FakeSiteDir(site_dir)


def _docs(tmp_path, rules_map=MAP, page=PAGE):
    docs = tmp_path / "docs"
    (docs / "manual-2-etap").mkdir(parents=True)
    (docs / "manual-2-etap" / "05b.md").write_text(page, encoding="utf-8")
    (docs / "site" / "hooks" / "helper").mkdir(parents=True)
    (docs / "site" / "hooks" / "helper" / "version.txt").write_text("0.3.1\n", encoding="utf-8")
    import yaml
    (docs / "site" / "hooks" / "helper" / "rules-map.yml").write_text(
        yaml.safe_dump(rules_map, allow_unicode=True), encoding="utf-8")
    return docs


def test_frame_border_text_examples_and_url(tmp_path):
    rules = build_rules(_docs(tmp_path), MAP)
    r = rules["frame_border"]
    assert r["title"] == "Рамка"
    assert "Видео с рамками." in r["text"]
    assert "Рамка по краям видео не всегда означает брак — тонкая граница по краю кадра." in r["text"]
    assert "<div" not in r["text"] and "{:" not in r["text"] and "**" not in r["text"]
    assert "Картинка" not in r["text"]
    assert r["url"] == BASE_URL + "manual-2-etap/05b/#рамка"
    assert r["url"].endswith("#рамка")
    assert r["examples"] == [
        {"title": "Рамка справа", "url": "https://x/a.mp4"},
        {"title": "Локальный пример", "url": BASE_URL + "manual-2-etap/assets/b.mp4"},
    ]


def test_contains_selects_only_matching_blocks(tmp_path):
    rules = build_rules(_docs(tmp_path), MAP)
    r = rules["speed_change"]
    assert "Замедленное или ускоренное видео — недопустимо." in r["text"]
    assert "[Инструкция заказчика, 04.09.2026]" in r["text"]   # атрибуция остаётся
    assert "сгенерированными ИИ" not in r["text"]
    assert r["url"].endswith("#другое")
    assert r["examples"] == [{"title": "ускорение", "url": BASE_URL + "manual-2-etap/assets/s.mp4"}]


def test_strip_sources_removes_source_tags(tmp_path):
    rules = build_rules(_docs(tmp_path), MAP, strip_sources=True)
    assert "Инструкция заказчика" not in rules["speed_change"]["text"]
    assert "Замедленное или ускоренное видео — недопустимо." in rules["speed_change"]["text"]
    assert "Инструкция заказчика" not in rules["duration_limit"]["text"]
    assert "Максимальная длина исходного видео — 20 минут." in rules["duration_limit"]["text"]


def test_contains_on_top_heading_takes_following_source_tag(tmp_path):
    r = build_rules(_docs(tmp_path), MAP)["duration_limit"]
    assert r["text"].startswith("- Максимальная длина исходного видео — 20 минут.")
    assert "[Инструкция заказчика, 25.09.2026]" in r["text"]
    assert "Вступление" not in r["text"]
    assert "Видео с рамками" not in r["text"]


def test_missing_heading_raises_with_check_id(tmp_path):
    bad = dict(MAP, glasses={"page": "manual-2-etap/05b.md", "heading": "Нет такого",
                             "title": "Очки"})
    with pytest.raises(PluginError, match="glasses"):
        build_rules(_docs(tmp_path, bad), bad)


def test_contains_without_match_raises(tmp_path):
    bad = {"x": {"page": "manual-2-etap/05b.md", "heading": "Другое", "title": "X",
                 "contains": "нет такого текста"}}
    with pytest.raises(PluginError, match="x"):
        build_rules(_docs(tmp_path, bad), bad)


def test_duplicate_heading_slug_gets_suffix(tmp_path):
    page = "## Рамка\n\nПервая.\n\n### Рамка {: .x }\n\nВторая.\n"
    m = {"frame_border": {"page": "manual-2-etap/05b.md", "heading": "Рамка", "title": "Рамка",
                          "occurrence": 2}}
    r = build_rules(_docs(tmp_path, m, page), m)["frame_border"]
    assert r["text"] == "Вторая."
    assert r["url"].endswith("#рамка_1")


def test_long_text_is_not_truncated(tmp_path):
    para = "Слово " * 150
    page = "### Длинно\n\n" + "\n\n".join(f"Абзац {i}. {para.strip()}." for i in range(5)) + "\n"
    m = {"x": {"page": "manual-2-etap/05b.md", "heading": "Длинно", "title": "X"}}
    r = build_rules(_docs(tmp_path, m, page), m)["x"]
    assert len(r["text"]) > 3000
    assert "Абзац 4." in r["text"]


def test_heading_list_joins_sections(tmp_path):
    m = {"face_lost": {"page": "manual-2-etap/05b.md", "heading": ["Рамка", "Другое"],
                       "title": "Лицо", "contains": None}}
    r = build_rules(_docs(tmp_path, m), m)["face_lost"]
    assert "Видео с рамками." in r["text"] and "сгенерированными ИИ" in r["text"]
    assert r["url"].endswith("#рамка")     # ссылка - на первый раздел
    urls = [e["url"] for e in r["examples"]]
    assert "https://x/a.mp4" in urls and BASE_URL + "manual-2-etap/assets/s.mp4" in urls


def test_examples_from_other_section(tmp_path):
    m = {"camera_jump": {"page": "manual-2-etap/05b.md", "heading": "Другое", "title": "Камера",
                         "contains": "ускоренное",
                         "examples_from": [{"heading": "Рамка", "contains": "справа"}]}}
    r = build_rules(_docs(tmp_path, m), m)["camera_jump"]
    assert r["examples"] == [
        {"title": "ускорение", "url": BASE_URL + "manual-2-etap/assets/s.mp4"},
        {"title": "Рамка справа", "url": "https://x/a.mp4"},
    ]
    assert "Рамка справа" not in r["text"]


def test_missing_rules_map_raises(tmp_path):
    docs = _docs(tmp_path)
    (docs / "site" / "hooks" / "helper" / "rules-map.yml").unlink()
    with pytest.raises(PluginError, match="rules-map.yml"):
        on_post_build(FakeConfig(docs, tmp_path / "site" / "build"))


def test_table_and_html_list_become_plain_lines():
    md = ("<ul class=\"value-checklist\">\n<li>Мужчина</li>\n<li>Женщина</li>\n</ul>\n\n"
          "| Тип | Требования |\n|---|---|\n| **Речь** | Чистое |\n")
    text, _ = section_to_text(md, "manual-2-etap/x.md")
    assert text == "- Мужчина\n- Женщина\n\nТип | Требования\nРечь | Чистое"


def test_video_list_moves_to_examples_with_its_intro_and_source():
    md = ("Правило.\n\n**Калибровочные примеры:**\n\n"
          "- [Пример А](https://x/a.mp4).\n- [](https://x/b.mp4)\n"
          "- ![grid: картинка](assets/c.jpeg)\n\n`[Источник примеров]`\n\n"
          "<ul class=\"dash-list\" markdown=\"1\">\n<li markdown=\"1\">\n\n"
          "пункт из HTML-списка;\n\n</li>\n</ul>\n")
    text, examples = section_to_text(md, "manual-2-etap/x.md")
    assert text == "Правило.\n\n- пункт из HTML-списка;"
    assert examples == [{"title": "Пример А", "url": "https://x/a.mp4"},
                        {"title": "Пример", "url": "https://x/b.mp4"}]


def test_youtube_and_vk_links_are_examples():
    md = "Текст [ролик](https://www.youtube.com/watch?v=1) и [вк](https://vkvideo.ru/video-1_2).\n"
    _, examples = section_to_text(md, "manual-2-etap/x.md")
    assert [e["title"] for e in examples] == ["ролик", "вк"]


def test_on_post_build_writes_rules_and_version(tmp_path):
    docs = _docs(tmp_path)
    site = tmp_path / "site" / "build"
    on_post_build(FakeConfig(docs, site))
    data = json.loads((site / "assessor-helper" / "rules.json").read_text(encoding="utf-8"))
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["generated"])
    assert set(data["rules"]) == set(MAP)
    ver = json.loads((site / "assessor-helper" / "version.json").read_text(encoding="utf-8"))
    assert ver == {"version": "0.3.1"}


def test_on_post_build_noop_on_pdf(tmp_path):
    docs = _docs(tmp_path)
    site = tmp_path / "site" / "build-pdf"
    on_post_build(FakeConfig(docs, site))
    assert not (site / "assessor-helper").exists()


def test_on_post_build_checks_anchor_in_built_html(tmp_path):
    docs = _docs(tmp_path)
    site = tmp_path / "site" / "build"
    page_dir = site / "manual-2-etap" / "05b"
    page_dir.mkdir(parents=True)
    (page_dir / "index.html").write_text('<h3 id="рамка-1">Рамка</h3>', encoding="utf-8")
    with pytest.raises(PluginError, match="frame_border"):
        on_post_build(FakeConfig(docs, site))


# --- реальный map и реальный мануал ---

def _code_check_ids():
    """Все check_id, которые выдаёт код: первый строковый аргумент Finding(...), _res(...),
    _or_none(...), _none_found(...) в findings.py и segment_check.py + MANUAL_CHECKS."""
    code = REPO / "assessor-helper" / "helper" / "analysis"
    if not code.is_dir():
        pytest.skip("кода программы нет (он только на компьютере разработки, не в репозитории)")
    ids = set()
    for name in ("findings.py", "segment_check.py"):
        src = (code / name).read_text(encoding="utf-8")
        ids.update(re.findall(r'\b(?:Finding|_res|_or_none|_none_found)\(\s*"([a-z_]+)"', src))
        m = re.search(r"MANUAL_CHECKS[^=]*=\s*\[(.*?)\]", src, re.S)
        if m:
            ids.update(re.findall(r'"([a-z_]+)"', m.group(1)))
    # проверка самой регулярки: эти точно есть в коде (в т.ч. многострочный вызов)
    assert {"duration_limit", "head_angle", "seg_pause", "broken_but_candidates",
            "seg_overlap", "field_singing"} <= ids, ids
    return sorted(ids)


def test_real_map_covers_every_check_id():
    rules_map = load_rules_map(REPO)
    missing = [c for c in _code_check_ids() if c not in rules_map]
    assert not missing, missing


def test_real_map_builds_from_real_manual():
    rules = build_rules(REPO, load_rules_map(REPO))
    for cid, r in rules.items():
        assert r["title"] and len(r["text"]) > 20, cid
        assert r["url"].startswith(BASE_URL + "manual-2-etap/"), cid
        assert "<" not in r["text"] and "{:" not in r["text"], (cid, r["text"][:200])
    assert any(e["url"].endswith("RHxn1GFTIeo.mp4") for e in rules["glasses"]["examples"])
    assert "естественно опущенные" in rules["eyes_closed"]["text"]
    assert rules["seg_cut_margin"]["url"].endswith("#отступ-от-склейки")
    assert rules["field_gender"]["url"].endswith("#1-пол")
    # тексты не обрезаются
    assert "Диалог (ответы на вопросы)" in rules["field_speech_type"]["text"]
    assert "Монолог (спонтанный)" in rules["field_speech_type"]["text"]
    assert "потеря лица — это когда человек повернул голову ещё дальше" in rules["head_angle"]["text"]
    # eyes_closed: оба исключения, а не «Ещё одно исключение» без первого
    assert "наклонился почитать книгу" in rules["eyes_closed"]["text"]
    # face_lost: поворот головы и смена кадра без человека
    for cid in ("face_lost", "seg_face_lost"):
        assert "нос «уходит за угол»" in rules[cid]["text"]
        assert "человек исчезает из кадра" in rules[cid]["text"]
        assert rules[cid]["url"].endswith("#потеря-лица")
    for cid in ("camera_jump", "seg_camera_jump"):
        assert any("Скачок камеры на 1:19" in e["title"] for e in rules[cid]["examples"])
    assert "Правильно | Неправильно" not in rules["seg_overlap"]["text"]


def test_read_version_from_real_repo():
    assert re.fullmatch(r"\d+\.\d+\.\d+", read_version(REPO))

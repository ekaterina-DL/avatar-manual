from pathlib import Path

from pymdownx.slugs import slugify as _pymdownx_slugify

from _section_utils import extract_section
from _list_utils import split_list_items

# Та же функция, что site/mkdocs.yml подключает для markdown_extensions.toc.slugify — иначе
# id, который реально проставит MkDocs на заголовок (например "темп-речи"), и якорь, который эта
# функция подставит в ссылку "→ ещё N прим.", могут разойтись, и клик по ссылке не долистает до
# нужного раздела (см. комментарий в mkdocs.yml — до этой правки заголовки из чистой кириллицы
# вообще получали нечитаемый id "_N", теперь оба места используют один и тот же алгоритм).
_slugify_heading = _pymdownx_slugify(case="lower")

DOCS_DIR = Path(__file__).resolve().parents[2]

# Явная таблица соответствий: где на целевой странице вставить превью, и откуда его взять.
# position="after_line" — сразу после строки, содержащей anchor; "before_line" — прямо перед ней.
MAPPINGS = [
    {
        # Каждое поле классификатора теперь своя ### -секция (12.08.2026, правка "выделить
        # каждый раздел визуально") — якоримся на заголовок СЛЕДУЮЩЕГО поля, а не на текст
        # содержимого самого поля "Темп речи": так вставка не зависит от того, как именно
        # переносится строка со значениями/цитатой внутри поля.
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "### Язык и акценты",
        "position": "before_line",
        "source_file": "manual-2-etap/11-example-library.md",
        "source_heading": "Темп речи",
        "max_items": 3,
        "label": "Темп речи",
    },
    {
        # Якоримся на заголовок СЛЕДУЮЩЕГО поля ("Тип речи"), а не на абзац "Смена эмоций
        # внутри одного ролика" внутри самой секции — тот же баг, что уже был у "Тип речи"
        # (см. комментарий там): anchor на параграф ВНУТРИ секции с position="before_line"
        # вставляет превью ПЕРЕД этим параграфом, а не в конец секции — пользователь заметил
        # 20.08.2026, что абзац "Смена эмоций..." на живом сайте рендерился ПОСЛЕ карточек,
        # хотя должен быть перед ними (сразу за "Важно, откуда именно определяется эмоция").
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "### Тип речи",
        "position": "before_line",
        "source_file": "manual-2-etap/11-example-library.md",
        "source_heading": "Эмоции",
        "max_items": 3,
        "label": "Эмоции",
    },
    {
        # Якоримся на заголовок СЛЕДУЮЩЕГО поля ("Темп речи"), а не на "### Тип речи" самого
        # поля — иначе превью вставляется перед началом секции "Тип речи" и визуально попадает
        # в хвост ПРЕДЫДУЩЕЙ секции "Эмоции и выражение лица" (см. комментарий выше и баг,
        # найденный пользователем 20.08.2026: 5 карточек с подписью "Тип речи" рендерились в
        # самом низу раздела "Эмоции и выражение лица", а не в разделе "Тип речи").
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "### Темп речи",
        "position": "before_line",
        # Видео зашиты прямо здесь ("items"), а не читаются из 11-example-library.md — раньше
        # был отдельный раздел "Тип речи: диалог, монолог и закадровый голос" на странице "Банк
        # примеров", но 20.08.2026 пользователь попросила его убрать целиком: он дословно
        # дублировал то, что и так показывается превью на странице классификатора, и не нёс
        # самостоятельной ценности как отдельная страница для чтения. См. _build_preview_markdown()
        # ниже — при наличии ключа "items" секция-источник не читается вовсе. max_items должен
        # равняться len(items), иначе сработает ветка "remaining > 0", которая для такого
        # mapping не имеет смысла (ссылаться там "ещё N примеров" уже некуда).
        #
        # Источники видео (для истории, подробный разбор — в _sources-log.md, запись #66):
        # - Монолог (подготовленный): `[ОС заказчика, 23.07.2026]` — видео aEUPBI6wMrA (тот же
        #   ролик, что раньше разбирался в 07-faq.md) и Quetk0Y2Rxo. Правило "одно видео — одно
        #   место, если у него нет разных комментариев под разные группы" (20.08.2026): оба этих
        #   видео в 10-qa-log.md несли ровно один, узкоспециальный комментарий про тип речи —
        #   строки для них оттуда удалены, единственное место теперь здесь.
        # - Монолог (спонтанный): `[ОС заказчика, 17.07.2026]` (видео _EmqHIjlEto — сегмент
        #   0:45.5–0:59.4, после исключения закадрового голоса из более раннего сегмента того же
        #   ролика) и `[Видео с разбором ошибок — Аватар 2 этап]` (спортивное интервью, видео
        #   -129135849_456240701, куратор на записи прямо называет это "монолог неподготовленный").
        # - Диалог: `[Разметка ВК видео — диалоги и закадровый голос]`.
        "items": [
            "- **Монолог (подготовленный):**\n"
            "  [пример 1](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/kandi_de_team/post_train/pre_stage/video/avatars/0f94c3c1-fc56-4da4-be41-6c39299fb51a/downloaded_raw/aEUPBI6wMrA.mp4),\n"
            "  [пример 2](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/kandi_de_team/post_train/pre_stage/video/avatars/0f94c3c1-fc56-4da4-be41-6c39299fb51a/downloaded_raw/Quetk0Y2Rxo.mp4)",
            "- **Монолог (спонтанный) (закадровый голос не учитываем):**\n"
            "  [пример 1](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/kandi_de_team/post_train/pre_stage/video/avatars/224c5e31-c351-45dc-a99e-bd38a9660201/downloaded_raw/_EmqHIjlEto.mp4),\n"
            "  [пример 2](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/vk/05_02_2026/-129135849_456240701/-129135849_456240701.mp4)",
            "- **Диалог (ответы на вопросы):**\n"
            "  [пример 1](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/vk/13_02_2026/-219726985_456239131/-219726985_456239131.mp4),\n"
            "  [пример 2](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/vk/16_02_2026/-72226886_456253999/-72226886_456253999.mp4)",
        ],
        "max_items": 3,
        "label": "Тип речи",
    },
    {
        # Якоримся на заголовок СЛЕДУЮЩЕГО поля ("Группа данных") — см. комментарий у "Тип речи"
        # выше про anchor на заголовок следующей секции при position="before_line".
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "### Группа данных",
        "position": "before_line",
        # Видео зашиты прямо здесь ("items"): отдельного раздела в 11-example-library.md для
        # "Язык и акценты" никогда не было, а по всему проекту нашлось только 3 видео с
        # упоминанием языка вообще — все три изначально были строками в 10-qa-log.md (журнал
        # проверок ОС, 23.07.2026 и 25.05 СТ2).
        #
        # Правило "одно видео — одно место, если у него нет разных комментариев под разные
        # группы" (20.08.2026): A5imdLsdnpU и NLPG_ic_sVg несли в журнале ровно один
        # узкоспециальный комментарий про язык — строки для них удалены из 10-qa-log.md, теперь
        # единственное место — здесь. Sf-tjXevlyQ в журнале остался: его строка там объединяет
        # 3 РАЗНЫХ замечания (язык + пол + качество кадра в полный рост) под разные поля
        # классификатора — это ровно тот случай, когда дублирование допустимо, если в каждом
        # месте — свой, непохожий комментарий (здесь ниже — только про язык, в журнале — все 3).
        #
        # Правильное значение для всех трёх подтверждено пользователем 20.08.2026: A5imdLsdnpU —
        # "английский"; NLPG_ic_sVg и Sf-tjXevlyQ — "другой" (в источнике исходно было только
        # "не английский" без уточнения, пользователь дополнила правильным значением).
        "items": [
            "- **Английский:**\n"
            "  [пример](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/kandi_de_team/post_train/pre_stage/video/avatars/0f94c3c1-fc56-4da4-be41-6c39299fb51a/downloaded_raw/A5imdLsdnpU.mp4)",
            "- **Язык определён неверно (надо указывать не Английский, а Другой):**\n"
            "  [пример 1](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/kandi_de_team/post_train/pre_stage/video/avatars/0f94c3c1-fc56-4da4-be41-6c39299fb51a/downloaded_raw/NLPG_ic_sVg.mp4),\n"
            "  [пример 2](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/22_05_2026/Sf-tjXevlyQ/Sf-tjXevlyQ.mp4)",
        ],
        "max_items": 2,
        "label": "Язык и акценты",
    },
    {
        # Якоримся на заголовок СЛЕДУЮЩЕГО поля ("Количество людей...") — см. комментарий у
        # "Тип речи" выше про anchor на заголовок следующей секции при position="before_line".
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "### Количество людей, одновременно находящихся в кадре",
        "position": "before_line",
        # Видео зашиты прямо здесь ("items"). По полю "Группа данных" во всём проекте нашлось
        # только 2 видео с явной привязкой к значению, оба из 10-qa-log.md:
        # - 1Zf12nWGOtM ("Не отмечены руки. Группа данных — студия (Ok)") — изначально казался
        #   недоступным (403 Access Denied), но причина оказалась в опечатке даты в самой
        #   ссылке в 10-qa-log.md ("22_05_2026" вместо верного "15_05_2026" из исходного PDF
        #   "Разметка ВК видео - ОС 22.05 СТ2.pdf") — пользователь попросила показать источник
        #   и опечатка нашлась и исправлена там же, 20.08.2026. Комментарий в качестве примера
        #   здесь — только про "Студия" (в самом журнале акцент на руках, поле "Группа данных"
        #   там лишь побочное "Ok"-уточнение) — по правилу "одно видео — одно место, если нет
        #   разных комментариев" строка в 10-qa-log.md не трогалась: тема там другая (руки).
        # - cf4No5s6qFI ("естественная среда, естественный фон") — рабочая сразу.
        "items": [
            "- **Студия:**\n"
            "  [пример](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/1Zf12nWGOtM/1Zf12nWGOtM.mp4)",
            "- **Естественная среда:**\n"
            "  [пример](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/27_05_2026/cf4No5s6qFI/cf4No5s6qFI.mp4)",
        ],
        "max_items": 2,
        "label": "Группа данных",
    },
    {
        # Якоримся на заголовок СЛЕДУЮЩЕГО поля ("Баланс по пению/говорению") — см. комментарий
        # у "Тип речи" выше про anchor на заголовок следующей секции при position="before_line".
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "### Баланс по пению/говорению",
        "position": "before_line",
        # Видео зашиты прямо здесь ("items"). Оба видео на "Один человек" (cEZNKE2Iej0,
        # MbzweqS5chA) и одно на "Два и более человека" (dU00EuczOiA) переиспользованы из
        # 10-qa-log.md — их родные комментарии там про ДРУГИЕ поля (Объём и поза / Ракурс /
        # Тип речи), а "один человек"/"2 человека" в них лишь попутное уточнение. Это разрешённый
        # случай правила "одно видео — одно место" (20.08.2026): разные комментарии под разные
        # группы, поэтому строки в 10-qa-log.md не трогали, а здесь у каждого — свой, отдельный
        # комментарий. cEZNKE2Iej0 и MbzweqS5chA заодно чинились по пути: в 10-qa-log.md у них
        # была опечатка в дате пути ссылки (22_05_2026 вместо верного 15_05_2026 из исходного PDF
        # "Разметка ВК видео - ОС 22.05 СТ2.pdf") — та же природа бага, что нашлась чуть раньше
        # у 1Zf12nWGOtM (см. запись "Группа данных" выше); тоже исправлено в 10-qa-log.md.
        #
        # S_ZtrMrSBQg (второе видео на "Два и более человека") был единственным, узкоспециальным
        # комментарием в 10-qa-log.md ("В кадре два человека.") — по правилу строка для него
        # оттуда удалена, единственное место теперь здесь.
        "items": [
            "- **Один человек в кадре:**\n"
            "  [пример 1](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/cEZNKE2Iej0/cEZNKE2Iej0.mp4),\n"
            "  [пример 2](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/MbzweqS5chA/MbzweqS5chA.mp4)",
            "- **Два и более человека в кадре:**\n"
            "  [пример 1](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/kandi_de_team/post_train/pre_stage/video/avatars/0f94c3c1-fc56-4da4-be41-6c39299fb51a/downloaded_raw/S_ZtrMrSBQg.mp4),\n"
            "  [пример 2](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/dU00EuczOiA/dU00EuczOiA.mp4)",
        ],
        "max_items": 2,
        "label": "Количество людей",
    },
    {
        # Якоримся на заголовок H2 "Частые ошибки классификатора" — у "Баланс по пению/говорению"
        # нет следующего ### поля (это последнее поле классификатора), поэтому анкор — ближайший
        # следующий заголовок вообще, тот же принцип, что у "Тип речи" выше про anchor на
        # заголовок следующей секции при position="before_line".
        "target_file": "manual-2-etap/04-classifier.md",
        "anchor": "## Частые ошибки классификатора",
        "position": "before_line",
        # Видео зашиты прямо здесь ("items"). Официальные примеры 1/2 из инструкции Kandinsky
        # (vkvideo.ru-ссылки, стр.2-3 "4. Примеры") НЕ используются здесь намеренно: embed_video_
        # links.py встраивает vkvideo.ru как <iframe>, а group_media_lists.py (сборка карточек в
        # .video-grid, см. этот файл) распознаёт для сетки только <video>-теги от embed_local_
        # media.py (.mp4-ссылки) — при смешении iframe и <video> в одном пункте списка "подпись
        # перед видео" ломается (raw_lead включает весь HTML iframe целиком и не совпадает с
        # _STRICT_LABEL_LEAD_RE), из-за чего пункт выпадает из сетки и рендерится необёрнутым
        # плеером с "осиротевшей" запятой рядом — обнаружено скриншотом при проверке 20.08.2026.
        # Поэтому оба значения ниже — только .mp4-ссылки с общего CDN, как и во всех остальных
        # полях на этой странице.
        #
        # "Речь" — aEUPBI6wMrA, тот же ролик, что уже используется в блоке "Тип речи" выше с
        # подписью "Монолог (подготовленный)": обычная речь без пения — валидный, хоть и попутный,
        # пример именно для ЭТОГО поля. Разрешённый случай правила "одно видео — одно место"
        # (20.08.2026): разные комментарии под разные поля классификатора, запись в блоке "Тип
        # речи" не трогалась.
        #
        # "Пение" — 3 реальных ошибки разметки из 10-qa-log.md (пользователь выбрала соотношение
        # 1+3, а не 1+1 или 1+2, т.к. по факту материала в журнале QA все 6 найденных там ошибок
        # этого поля — в одну сторону, "должно быть Пение, а стоит Речь"; обратных ошибок не
        # нашлось вовсе). У всех трёх ниже в журнале был ровно один, узкоспециальный комментарий
        # про это поле — строки для них удалены оттуда по правилу "одно видео — одно место",
        # единственное место теперь здесь:
        # - OjbDE5P1yM4 ("Пение, а не речь.")
        # - gdoKm-hSp5U ("Одновременно выбраны речь и пение") — иллюстрирует ⚠️ про
        #   взаимоисключающие варианты выше.
        # - PljgCCMJY40 (дословно цитировал критерий "с говорением: чистое, без превалирующих...
        #   музыки", а на фрагменте звучало громкое муз. сопровождение) — иллюстрирует, что
        #   доминирующая музыка означает "Пение", а не "Речь".
        "items": [
            "- **Речь:**\n"
            "  [пример](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/kandi_de_team/post_train/pre_stage/video/avatars/0f94c3c1-fc56-4da4-be41-6c39299fb51a/downloaded_raw/aEUPBI6wMrA.mp4)",
            "- **Пение:**\n"
            "  [пример 1](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/kandi_de_team/post_train/pre_stage/video/avatars/b59716e5-79dd-48ff-9971-27f31e4a63ea/downloaded_raw/OjbDE5P1yM4.mp4),\n"
            "  [пример 2](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/09_06_2026/gdoKm-hSp5U/gdoKm-hSp5U.mp4),\n"
            "  [пример 3](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/09_06_2026/PljgCCMJY40/PljgCCMJY40.mp4)",
        ],
        "max_items": 2,
        "label": "Баланс по пению/говорению",
    },
    {
        "target_file": "manual-3-etap/04-video-quality.md",
        "anchor": '## Когда сразу «Битое» (не отвечая на вопросы классификатора)',
        "position": "after_line",
        "source_file": "manual-3-etap/07-example-library.md",
        "source_heading": "1. Размечено битое видео (хотя должно было быть отправлено в «битое»)",
        "max_items": 3,
        "label": "Битое",
    },
    {
        "target_file": "manual-3-etap/04-video-quality.md",
        "anchor": '## Когда отмечать «Артефакт», но всё равно отвечать на вопросы',
        "position": "after_line",
        "source_file": "manual-3-etap/07-example-library.md",
        "source_heading": "2. Наличие артефакта (не проставлен)",
        "max_items": 3,
        "label": "Артефакт",
    },
]


def _build_preview_markdown(mapping):
    if "items" in mapping:
        # Видео зашиты прямо в MAPPINGS, не читаются со страницы — см. комментарий у записи
        # "Тип речи" выше. max_items там всегда равен len(items), поэтому ветка "remaining > 0"
        # ниже для такого mapping не сработает.
        items = mapping["items"]
    else:
        source_path = DOCS_DIR / mapping["source_file"]
        source_text = source_path.read_text(encoding="utf-8")
        section_body = extract_section(source_text, mapping["source_heading"])
        if section_body is None:
            return None
        items = split_list_items(section_body)
    if not items:
        return None
    preview_items = items[: mapping["max_items"]]
    remaining = len(items) - len(preview_items)
    # Приватный маркер для group_media_lists.py (следующий хук в пайплайне): превью вставляется
    # посреди прозы целевой страницы, без собственного markdown-заголовка — без этой строки
    # group_media_lists.py взял бы эйброу .video-block из ближайшего ПРЕДЫДУЩЕГО настоящего
    # заголовка целевой страницы (например, "Уточнения по конкретным полям..."), а не из
    # названия поля, которому реально посвящено превью. group_media_lists.py распознаёт эту
    # строку, использует её как current_heading именно с этой точки документа и вырезает саму
    # строку из финального вывода — она не должна попасть в HTML как видимый текст.
    lines = [
        "",
        f'<!-- video-eyebrow: {mapping["label"]} -->',
        '<div markdown="1">',
    ]
    if not mapping.get("skip_label"):
        lines.append("**Примеры из банка:**")
    lines.append("")
    lines.extend(preview_items)
    if remaining > 0:
        anchor = _slugify_heading(mapping["source_heading"], "-")
        link = f"{Path(mapping['source_file']).name}#{anchor}"
        lines.append(f"\n→ ещё {remaining} прим. в [банке примеров]({link})")
    # Пустая строка обязательна перед закрывающим </div> независимо от remaining: без неё, когда
    # remaining == 0 (превью показывает вообще все примеры раздела, "ещё N" не добавляется),
    # </div> оказывается на строке сразу после последнего пункта списка без пустой строки-разделителя
    # между ними. group_media_lists.py (следующий по порядку хук) сканирует список видео-пунктов и
    # останавливается только на пустой строке — без неё "</div>" ошибочно затягивается внутрь
    # последнего пункта как продолжение подписи, а _parse_video_item() затем кладёт этот "</div>"
    # прямо в caption, что даёт битую вложенность тегов на странице:
    # `<div class="vi-cap"><span markdown="1"></div></span></div>`. Обнаружено на
    # 04-classifier.md → превью "Ракурс" (ровно 2 примера в разделе-источнике = remaining 0).
    lines.append("")
    lines.append("</div>")
    lines.append("")
    return "\n".join(lines)


def _apply_mapping(markdown, mapping):
    preview = _build_preview_markdown(mapping)
    if preview is None:
        return markdown
    lines = markdown.split("\n")
    for idx, line in enumerate(lines):
        if mapping["anchor"] in line:
            insert_at = idx + 1 if mapping["position"] == "after_line" else idx
            new_lines = lines[:insert_at] + preview.split("\n") + lines[insert_at:]
            return "\n".join(new_lines)
    return markdown


def on_page_markdown(markdown, page, config, files):
    """Вставляет компактное превью (2-3 примера) из банка примеров рядом с конкретным полем
    классификатора/критерием — только там, где явно прописано соответствие в MAPPINGS. Ничего
    не выдумывает: если якорь или раздел-источник не найден, страница остаётся без изменений."""
    src_uri = page.file.src_uri.replace("\\", "/")
    applicable = [m for m in MAPPINGS if m["target_file"] == src_uri]
    if not applicable:
        return markdown
    for mapping in applicable:
        markdown = _apply_mapping(markdown, mapping)
    return markdown

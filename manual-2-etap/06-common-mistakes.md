# Частые ошибки

Шесть категорий ошибок, которые заказчик регулярно фиксирует при проверке разметки — с реальными
примерами. Полные правила по каждой теме — в профильных разделах мануала
([04-classifier.md](04-classifier.md), [02-segments.md](02-segments.md),
[«Что не размечаем / Битое»](05b-what-not-to-label.md)).

## 1. Ошибка классификатора

Значения классификатора должны быть согласованы между сегментами одного и того же человека и
соответствовать тому, что реально видно на видео, а не «по умолчанию»/предположению. Полные
правила заполнения — [04-classifier.md](04-classifier.md).

⚠️ **Поля неравнозначны по строгости.** Часть полей заказчик прямо признаёт оценочными
(например, освещение) — единого порога согласованности по ним нет, за них не «наказывают» так
строго. А вот **пол и язык** — поля с объективно проверяемым правильным ответом, не
«оценочные»: «неверный пол» в списке частых ошибок экзамена стоит в одном ряду с границами
сегмента и пропущенными склейками/водяными знаками (см.
[«Частые ошибки на экзамене»](00b-exam.md#частые-ошибки-на-экзамене)) — то есть заказчик
трактует такие ошибки как **грубые**, а не мягкие оценочные, и реагирует на них особенно
болезненно.

### Какие поля чаще всего ошибаются

**Объём и поза тела (руки)** — самая частая причина, примерно каждая третья ошибка
классификатора: не отмечены руки, когда кисти видны в кадре, либо наоборот — отмечены, хотя рук
не видно.

| Ссылка | Комментарий |
|---|---|
| [9hJQFpqKMFM](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/9hJQFpqKMFM/9hJQFpqKMFM.mp4) | Выбрано 2 пункта, нужно «голова, плечи и руки». |
| [IBOvZiZGiLs](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/IBOvZiZGiLs/IBOvZiZGiLs.mp4) | Не отмечены руки, хотя кисти видны в кадре. |
| [nIAKieiyOiU](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/27_05_2026/nIAKieiyOiU/nIAKieiyOiU.mp4) | Обратная ошибка: кисти рук не появляются ни разу — руки отмечены зря, нужно «Голова и плечи». |

**Тип речи: Монолог/Диалог** — вторая по частоте причина: диалог путают с монологом и наоборот.

| Ссылка | Комментарий |
|---|---|
| [IMAX12ePRaY](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/IMAX12ePRaY/IMAX12ePRaY.mp4) | В сегменте виден и говорит только один человек — нужно «Монолог». |
| [-DjyPczrPA8](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/-DjyPczrPA8/-DjyPczrPA8.mp4) | Если в сегменте поют/говорят несколько человек — это уже не монолог. |
| [HxZkUe-Cp1I](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/HxZkUe-Cp1I/HxZkUe-Cp1I.mp4) | Сегмент 0:10.01–0:21.36: если на видео поют/говорят несколько человек, то это уже не монолог. |

**Фон: Динамичный/уличный** — съёмка на улице сама по себе требует значения
«Динамичный/уличный», независимо от движения в кадре.

| Ссылка | Комментарий |
|---|---|
| [f8RqjBhyLUY](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/f8RqjBhyLUY/f8RqjBhyLUY.mp4) | Поставлен «естественный, но статичный» фон, хотя видео явно снято на улице. |
| [E1qZdo1x34E](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/E1qZdo1x34E/E1qZdo1x34E.mp4) | Уличный фон не отмечен. |

**Эмоции**

| Ссылка | Комментарий |
|---|---|
| [FmKbmmwKG2Y](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/FmKbmmwKG2Y/FmKbmmwKG2Y.mp4) | Отмечены положительные эмоции, но их в сегменте нет. |
| [kMQR3oRTu28](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/kMQR3oRTu28/kMQR3oRTu28.mp4) | Выбрана положительная эмоция — в кадре её не было. |

**Пол** — поле с объективно проверяемым ответом; заказчик реагирует на такие ошибки особенно
болезненно (см. [04-classifier.md](04-classifier.md#1-пол)).

| Ссылка | Комментарий |
|---|---|
| [q2xRRS6Du2E](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/q2xRRS6Du2E/q2xRRS6Du2E.mp4) | Выбран пол «мужской» (неверно). |
| [GcOMjP37wB0](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/GcOMjP37wB0/GcOMjP37wB0.mp4) | Поставлено, что на видео женщина (неверно). |

Реже встречаются ошибки в полях «Ракурс», «Язык» и «Возраст» — тот же принцип: значение должно
быть одно и соответствовать тому, что реально видно/слышно на видео, а не меняться произвольно
между сегментами одного человека.

## 2. Некорректные границы объекта

Сегмент должен начинаться с начала речи человека и заканчиваться, когда он перестаёт говорить —
не ставить границы произвольно. Самая частая причина в этой категории — необрезанное длительное
молчание в начале, конце или внутри сегмента. Подробнее —
[02-segments.md](02-segments.md#определение-и-границы).

| Ссылка | Комментарий |
|---|---|
| [MAhIUIkXhiM](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/MAhIUIkXhiM/MAhIUIkXhiM.mp4) | Сегмент не должен содержать длительное молчание внутри (здесь — с 15 до 22 сек). |
| [b-9pXhZERTQ](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/b-9pXhZERTQ/b-9pXhZERTQ.mp4) | На 1:02 лицо исчезло из кадра — нужно разделить на два сегмента. |
| [Tn6Vw9gArvU](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/Tn6Vw9gArvU/Tn6Vw9gArvU.mp4) | Сегмент начат поздно, закончен рано — начинать нужно с начала речи. |
| [vtT78TfDfXU](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/vtT78TfDfXU/vtT78TfDfXU.webm) | Достаточно завершить на 37 сек — дальше длительные всхлипы, лицо закрыто руками. |

## 3. Не размечен объект / ошибочно отправлено в «Битое»

Прежде чем ставить «Битое», нужно убедиться, что во всём видео действительно нет ни одного
фрагмента ≥10 сек с говорящим/поющим человеком в нужном качестве. Это самая частая формулировка
ошибки в этой категории.

| Ссылка | Комментарий |
|---|---|
| [ZNXBMI0Feq8](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/ZNXBMI0Feq8/ZNXBMI0Feq8.mp4) | Качество видео подходит — не размечен подходящий под ТЗ сегмент. |
| [plcDpLhYeYo](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/plcDpLhYeYo/plcDpLhYeYo.mp4) | Качество хорошее — можно выделить несколько сегментов (голова; голова/плечи/руки). |
| [BTFz3q2Ho_g](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/BTFz3q2Ho_g/BTFz3q2Ho_g.mp4) | Видео ошибочно отправлено в «Битое». Не размечен подходящий сегмент: 0:28–0:38. |
| [-pqNntbAza0](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/-pqNntbAza0/-pqNntbAza0.mp4) | Выделено недостаточное количество сегментов — не выделен сегмент с крупным планом (с 2:17). |
| [GM6jMaElkUg](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/GM6jMaElkUg/GM6jMaElkUg.mp4) | Выделено недостаточное количество сегментов — не выделен сегмент с другим ракурсом (~с 1:36). |
| [-fTRRZqIY2s](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/-fTRRZqIY2s/-fTRRZqIY2s.mp4) | Подходящий сегмент 0:40.79–1:16.24. Короткий закадровый смех — не повод пропускать сегмент целиком. |

## 4. Смена кадра/склейка (включая водяной знак и наложенный текст)

Сегмент не должен содержать склейку, смену кадра, водяной знак или наложенный текст. Водяной
знак может быть малозаметен в начале — проверять нужно видео целиком, а не только первые секунды.

| Ссылка | Комментарий |
|---|---|
| [31YbqD2D0Og](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/31YbqD2D0Og/31YbqD2D0Og.mp4) | На протяжении всего видео справа внизу есть водяной знак. |
| [lZz8V-mG098](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/lZz8V-mG098/lZz8V-mG098.mp4) | Склейка в сегменте 1:58–2:09 (между 2:03–2:04). |
| [TiEu8a-diLU](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/TiEu8a-diLU/TiEu8a-diLU.mp4) | Тёмный водяной знак справа внизу заметен только с 0:28 — присутствует на протяжении всего видео. |
| [FAhUrrvwWPQ](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/FAhUrrvwWPQ/FAhUrrvwWPQ.mp4) | Склейка в начале сегмента: человек отворачивается и закрывает лицо книгой. |
| [vo9SszmXBG8](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/18_05_2026/vo9SszmXBG8/vo9SszmXBG8.mp4) | Сегмент содержит наложение кадров. |

## 5. Нечёткость мимики/черт лица

Отдельная категория для случаев, когда человек снят слишком близко к камере или в движении, из-за
чего черты лица/мимика расфокусированы («мыльность»), даже если формально разрешение видео в
порядке. Триггер — не только близкая съёмка: тряска (в т.ч. в движущемся транспорте) и резкий
зум дают тот же эффект. См. [«Что не размечаем / Битое»](05b-what-not-to-label.md).

| Ссылка | Комментарий |
|---|---|
| [Sb5GOcoiO2I](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/27_05_2026/Sb5GOcoiO2I/Sb5GOcoiO2I.mp4) | Во время движения авто по кочкам теряется чёткость — нужно было найти фрагмент без тряски. |
| [Lr-2wA_U1ws](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/Lr-2wA_U1ws/Lr-2wA_U1ws.mp4) | Нет чёткости в обоих сегментах + резкий зум во втором сегменте. |
| [-pqNntbAza0](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/-pqNntbAza0/-pqNntbAza0.mp4) | Расфокус в середине сегмента нужно было вырезать. |
| [lgSORdR0UWs](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/kandi_de_team/post_train/pre_stage/video/avatars/224c5e31-c351-45dc-a99e-bd38a9660201/downloaded_raw/lgSORdR0UWs.mp4) | Недостаточная чёткость при слишком близком расположении человека к камере — расфокус («мыльность»). |

## 6. Иное

Всё остальное: превышение допустимой длины исходного видео (см.
[«Что не размечаем / Битое»](05b-what-not-to-label.md)), лишние однотипные сегменты (см.
[«Когда объединять/делить сегмент»](02-segments.md#когда-объединятьделить-сегмент)),
неподходящий фоновый звук, сегмент и «Битое» отмечены одновременно (см.
[«Как правильно отправить в „Битое“ технически»](05b-what-not-to-label.md)).

| Ссылка | Комментарий |
|---|---|
| [YSTAtJFljnU](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/YSTAtJFljnU/YSTAtJFljnU.mp4) | Выделено 4 однотипных сегмента вместо допустимых 1-2. |

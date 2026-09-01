# Частые ошибки

Шесть категорий ошибок, которые заказчик регулярно фиксирует при проверке разметки — с реальными
примерами. Полные правила по каждой теме — в профильных разделах мануала
([04-classifier.md](04-classifier.md), [02-segments.md](02-segments.md),
[«Что не размечаем / Битое»](05b-what-not-to-label.md)).

## Что заказчик считает грубой ошибкой, а что нет

Заказчик прямо разделяет два уровня требований:

1. **Выбор сегмента** — границы, не пропустить водяной знак/рамку/склейку, найти подходящий
   «золотой кадр» среди монтажа. Требования **жёсткие**, и именно здесь чаще всего прилетают
   серьёзные ошибки.
2. **Заполнение классификатора** — пол, возраст, поза, фон, эмоции, тип речи и т.д.
   Формального порога согласованности между асессорами нет, многие поля прямо признаны
   **оценочными**.

`[Видео с разбором ошибок — Аватар 2 этап]`

Из ОС заказчик прямо называл **«грубыми ошибками»**, например:

- сегмент размечен со склейкой внутри;
- видео отправлено в «Битое», хотя на нём был подходящий сегмент.

Отсюда практический вывод — к **грубым** тянутся ошибки категорий «Не размечен объект /
ошибочно отправлено в „Битое“» и «Смена кадра/склейка» ниже: то, что портит сам сегмент или
пропускает брак видео. К **некритичным** — ошибки классификатора: неверно выбранное поле при в
целом верно найденном сегменте.

⚠️ **Исключение — пол и язык.** Формально это тоже поля классификатора, но заказчик проверяет
их так же строго, как границы и склейки: это поля с объективно проверяемым ответом, не
«оценочные» (в отличие, например, от освещения). «Неверный пол» относится к числу самых частых
ошибок наравне с границами сегмента и пропущенными склейками/водяными знаками — заказчик
реагирует на такие ошибки особенно болезненно, несмотря на их формальную «классификаторскую»
природу.

## 1. Ошибка классификатора

Значения классификатора должны быть согласованы между сегментами одного и того же человека и
соответствовать тому, что реально видно на видео, а не «по умолчанию»/предположению. Полные
правила заполнения — [04-classifier.md](04-classifier.md).

### Какие поля чаще всего ошибаются

**Объём и поза тела (руки)** — самая частая причина, примерно каждая третья ошибка
классификатора: не отмечены руки, когда кисти видны в кадре, либо наоборот — отмечены, хотя рук
не видно.

<!-- video-eyebrow: Объём и поза тела (руки) -->
- [Выбрано 2 пункта, нужно «голова, плечи и руки».](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/9hJQFpqKMFM/9hJQFpqKMFM.mp4)
- [Не отмечены руки, хотя кисти видны в кадре.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/IBOvZiZGiLs/IBOvZiZGiLs.mp4)
- [Обратная ошибка: кисти рук не появляются ни разу — руки отмечены зря, нужно «Голова и плечи».](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/27_05_2026/nIAKieiyOiU/nIAKieiyOiU.mp4)
- [Выбрано 2 значения в «Объём и поза тела» при одном человеке в кадре.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/cEZNKE2Iej0/cEZNKE2Iej0.mp4)
- [Поставлено «голова и плечи», хотя в кадре появляется рука — нужно «голова, плечи и руки».](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/27_05_2026/gR54YHpUgBA/gR54YHpUgBA.mp4)
- [Кисти рук видны в кадре, но не отмечены.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/22_05_2026/W-YXdArqqc8/W-YXdArqqc8.mp4)
- [Ещё один пропуск: руки видны, а в классификаторе это не отражено.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/18_05_2026/CTTnDNAE-Hs/CTTnDNAE-Hs.mp4)
- [Работает и в обратную сторону: в одном фрагменте руки видны, в другом — нет, это повод для отдельных сегментов, а не одного общего.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/18_05_2026/WHhBV7giNlA/WHhBV7giNlA.mp4)

**Тип речи: Монолог/Диалог** — вторая по частоте причина: диалог путают с монологом и наоборот.

<!-- video-eyebrow: Тип речи: Монолог/Диалог -->
- [В сегменте виден и говорит только один человек — нужно «Монолог».](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/IMAX12ePRaY/IMAX12ePRaY.mp4)
- [Если в сегменте поют/говорят несколько человек — это уже не монолог.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/-DjyPczrPA8/-DjyPczrPA8.mp4)
- [Сегмент 0:10.01–0:21.36: если на видео поют/говорят несколько человек, то это уже не монолог.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/HxZkUe-Cp1I/HxZkUe-Cp1I.mp4)
- [Поют или говорят несколько человек, а отмечен «монолог».](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/3rxiy3yAsKQ/3rxiy3yAsKQ.mp4)

**Фон: Динамичный/уличный** — съёмка на улице сама по себе требует значения
«Динамичный/уличный», независимо от движения в кадре.

<!-- video-eyebrow: Фон: Динамичный/уличный -->
- [Поставлен «естественный, но статичный» фон, хотя видео явно снято на улице.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/f8RqjBhyLUY/f8RqjBhyLUY.mp4)
- [Уличный фон не отмечен.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/E1qZdo1x34E/E1qZdo1x34E.mp4)
- [Выбрано 2 значения в поле «Фон» при одном человеке в кадре.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/eZvc533RNP8/eZvc533RNP8.mp4)

**Эмоции**

<!-- video-eyebrow: Эмоции -->
- [Отмечены положительные эмоции, но их в сегменте нет.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/FmKbmmwKG2Y/FmKbmmwKG2Y.mp4)
- [Выбрана положительная эмоция — в кадре её не было.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/kMQR3oRTu28/kMQR3oRTu28.mp4)
- [Эмоции явно не нейтральные, а поставлены «спокойные»/«нейтральные».](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/22_05_2026/x45XHocta7o/x45XHocta7o.mp4)

**Пол** — поле с объективно проверяемым ответом; заказчик реагирует на такие ошибки особенно
болезненно (см. [04-classifier.md](04-classifier.md#1-пол)).

<!-- video-eyebrow: Пол -->
- [Выбран пол «мужской» (неверно).](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/q2xRRS6Du2E/q2xRRS6Du2E.mp4)
- [Поставлено, что на видео женщина (неверно).](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/GcOMjP37wB0/GcOMjP37wB0.mp4)

Реже встречаются ошибки в полях «Ракурс», «Язык», «Темп речи» и «Возраст» — тот же принцип:
значение должно быть одно и соответствовать тому, что реально видно/слышно на видео, а не
меняться произвольно между сегментами одного человека.

<!-- video-eyebrow: Ракурс, язык, темп речи -->
- [Выбрано 2 значения в «Преобладающем ракурсе» — нужно выбрать один, доминирующий вариант.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/MbzweqS5chA/MbzweqS5chA.mp4)
- [Неверно выбран язык сегмента.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/8F8h03d5JjA/8F8h03d5JjA.mp4)
- [2 значения в «Темпе речи» в одном сегменте у одного и того же человека.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/aR-8xggopRc/aR-8xggopRc.mp4)

## 2. Некорректные границы объекта

Сегмент должен начинаться с начала речи человека и заканчиваться, когда он перестаёт говорить —
не ставить границы произвольно. Самая частая причина в этой категории — необрезанное длительное
молчание в начале, конце или внутри сегмента. Подробнее —
[02-segments.md](02-segments.md#определение-и-границы).

- [Сегмент не должен содержать длительное молчание внутри (здесь — с 15 до 22 сек).](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/MAhIUIkXhiM/MAhIUIkXhiM.mp4)
- [На 1:02 лицо исчезло из кадра — нужно разделить на два сегмента.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/b-9pXhZERTQ/b-9pXhZERTQ.mp4)
- [Сегмент начат поздно, закончен рано — начинать нужно с начала речи.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/Tn6Vw9gArvU/Tn6Vw9gArvU.mp4)
- [Достаточно завершить на 37 сек — дальше длительные всхлипы, лицо закрыто руками.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/vtT78TfDfXU/vtT78TfDfXU.webm)
- [Сегмент начат на несколько секунд позже, чем нужно: подходящая граница была уже на 0:47 (или 1:25), закончить можно было на 1:48.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/oR3b16-CtvY/oR3b16-CtvY.mp4)
- [Сегмент поставлен впритык к склейке кадра — нужно отступить от границы монтажа.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/RvGHVoJ8lIA/RvGHVoJ8lIA.mp4)
- [Размеченный сегмент 3:24–3:58: в конце больше 2 секунд молчания, нужно обрезать раньше, ровно на последнем слове.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/ZzTyBpl8sfw/ZzTyBpl8sfw.mp4)
- [Микрофон закрывает рот, а в конце человек уходит из кадра — подходящий сегмент 0:39–0:51.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/-3XnjZqdOrQ/-3XnjZqdOrQ.mp4)

## 3. Не размечен объект / ошибочно отправлено в «Битое»

Прежде чем ставить «Битое», нужно убедиться, что во всём видео действительно нет ни одного
фрагмента ≥10 сек с говорящим/поющим человеком в нужном качестве. Это самая частая формулировка
ошибки в этой категории.

- [Качество видео подходит — не размечен подходящий под ТЗ сегмент.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/ZNXBMI0Feq8/ZNXBMI0Feq8.mp4)
- [Качество хорошее — можно выделить несколько сегментов (голова; голова/плечи/руки).](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/plcDpLhYeYo/plcDpLhYeYo.mp4)
- [Видео ошибочно отправлено в «Битое». Не размечен подходящий сегмент: 0:28–0:38.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/BTFz3q2Ho_g/BTFz3q2Ho_g.mp4)
- [Выделено недостаточное количество сегментов — не выделен сегмент с крупным планом (с 2:17).](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/-pqNntbAza0/-pqNntbAza0.mp4)
- [Выделено недостаточное количество сегментов — не выделен сегмент с другим ракурсом (~с 1:36).](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/GM6jMaElkUg/GM6jMaElkUg.mp4)
- [Подходящий сегмент 0:40.79–1:16.24. Короткий закадровый смех — не повод пропускать сегмент целиком.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/-fTRRZqIY2s/-fTRRZqIY2s.mp4)
- [Видео отправлено в «Битое», хотя подходящий по качеству сегмент есть: лёгкая зернистость сама по себе не брак.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/UAPAmMyPmDo/UAPAmMyPmDo.mp4)
- [Сегмент выделен и одновременно стоит галочка «Битое» — так нельзя, это взаимоисключающие ответы.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/22_05_2026/tXi-fVey5BY/tXi-fVey5BY.mp4)
- [Рассинхронизация звука и движения губ (липсинк) — законный повод для «Битого».](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/22_05_2026/mlZdpX2-xTc/mlZdpX2-xTc.mp4)
- [Видео помечено «Битым» без реальных дефектов, хотя качество позволяет разметить сегмент.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/22_05_2026/ZfWOn8RU9qg/ZfWOn8RU9qg.mp4)

## 4. Смена кадра/склейка (включая водяной знак и наложенный текст)

Сегмент не должен содержать склейку, смену кадра, водяной знак или наложенный текст. Водяной
знак может быть малозаметен в начале — проверять нужно видео целиком, а не только первые секунды.

- [На протяжении всего видео справа внизу есть водяной знак.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/31YbqD2D0Og/31YbqD2D0Og.mp4)
- [Склейка в сегменте 1:58–2:09 (между 2:03–2:04).](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/lZz8V-mG098/lZz8V-mG098.mp4)
- [Тёмный водяной знак справа внизу заметен только с 0:28 — присутствует на протяжении всего видео.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/TiEu8a-diLU/TiEu8a-diLU.mp4)
- [Склейка в начале сегмента: человек отворачивается и закрывает лицо книгой.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/FAhUrrvwWPQ/FAhUrrvwWPQ.mp4)
- [Сегмент содержит наложение кадров.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/18_05_2026/vo9SszmXBG8/vo9SszmXBG8.mp4)

## 5. Нечёткость мимики/черт лица

Отдельная категория для случаев, когда человек снят слишком близко к камере или в движении, из-за
чего черты лица/мимика расфокусированы («мыльность»), даже если формально разрешение видео в
порядке. Триггер — не только близкая съёмка: тряска (в т.ч. в движущемся транспорте) и резкий
зум дают тот же эффект. См. [«Что не размечаем / Битое»](05b-what-not-to-label.md).

- [Во время движения авто по кочкам теряется чёткость — нужно было найти фрагмент без тряски.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/27_05_2026/Sb5GOcoiO2I/Sb5GOcoiO2I.mp4)
- [Нет чёткости в обоих сегментах + резкий зум во втором сегменте.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/Lr-2wA_U1ws/Lr-2wA_U1ws.mp4)
- [Расфокус в середине сегмента нужно было вырезать.](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/-pqNntbAza0/-pqNntbAza0.mp4)
- [Недостаточная чёткость при слишком близком расположении человека к камере — расфокус («мыльность»).](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/kandi_de_team/post_train/pre_stage/video/avatars/224c5e31-c351-45dc-a99e-bd38a9660201/downloaded_raw/lgSORdR0UWs.mp4)

## 6. Иное

Всё остальное: превышение допустимой длины исходного видео (см.
[«Что не размечаем / Битое»](05b-what-not-to-label.md)), лишние однотипные сегменты (см.
[«Когда объединять/делить сегмент»](02-segments.md#когда-объединятьделить-сегмент)),
неподходящий фоновый звук, сегмент и «Битое» отмечены одновременно (см.
[«Как правильно отправить в „Битое“ технически»](05b-what-not-to-label.md)).

**Пример:** выделено 4 однотипных сегмента вместо допустимых 1-2.

[Видео-пример](https://gigaeye-kandinsky-spark.obs.ru-moscow-1.hc.sbercloud.ru/ak/youtube/avatar/15_05_2026/YSTAtJFljnU/YSTAtJFljnU.mp4)

/**
 * Приёмник результатов тестирования по 2 этапу.
 * Разворачивается как веб-приложение (Расширения → Apps Script в целевой Google-таблице).
 * Инструкция: docs/quiz-apps-script.md
 */

// Должен совпадать с token в site/theme/quiz-config.js
var TOKEN = 'avatar-stage2-quiz';
var SHEET_NAME = 'Результаты';

function doGet() {
  return _json({ ok: true, hint: 'Приёмник работает. Данные принимаются только POST-запросом.' });
}

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    if (String(data.token) !== TOKEN) {
      return _json({ ok: false, error: 'bad token' });
    }
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sh = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
    if (sh.getLastRow() === 0) {
      sh.appendRow([
        'Дата и время', 'Фамилия', 'Имя', 'Процент', 'Верных из ' + (data.total || 15),
        'Вердикт', 'Неверные ответы', 'Длительность, сек', 'ID вопросов'
      ]);
    }
    var wrong = (data.wrongAnswers || []).map(function (w) {
      var chosen = (w.chosen === null || w.chosen === undefined) ? '— (не успел)' : w.chosen;
      return w.n + '. ' + w.question +
        '\n   выбрано: ' + chosen +
        '\n   верно: ' + w.correct +
        '\n   тема: ' + w.topic +
        '\n   раздел: ' + w.reviewUrl;
    }).join('\n\n');

    sh.appendRow([
      new Date(),
      data.surname || '',
      data.name || '',
      data.percent,
      data.correct,
      data.verdict || '',
      wrong,
      data.durationSec,
      (data.questionIds || []).join(', ')
    ]);
    return _json({ ok: true });
  } catch (err) {
    return _json({ ok: false, error: String(err) });
  }
}

function _json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

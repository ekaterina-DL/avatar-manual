/**
 * ================================================================
 *  ManualAccess.gs — меню «Доступ к мануалу».
 *  Выдаёт, сбрасывает, блокирует и разблокирует логины сайта-мануала
 *  (Assessor1, Assessor2...). В сайт уходит только логин вида Assessor7 —
 *  ФИО и почты из таблицы никуда не передаются.
 *
 *  Как поставить (в проекте уже есть свои скрипты и своя onOpen в Код.gs):
 *    1. «+» рядом с «Файлы» → «Скрипт», имя ManualAccess → вставить этот код.
 *    2. В Код.gs внутри function onOpen() { ... } перед последней «}»
 *       добавить строку:   manualAccessAddMenu();
 *    3. Сохранить, обновить таблицу, меню «Доступ к мануалу» →
 *       «Ввести секретный ключ».
 *
 *  Пункт «Отправить логин на почту» шлёт письмо с вашего Google-аккаунта
 *  на адрес из колонки «Почта Tagme». При первом запуске Google спросит
 *  разрешение «Отправлять письма от вашего имени» — его нужно дать.
 *
 *  Все имена здесь начинаются с manualAccess / MA_, чтобы не пересекаться
 *  с другими файлами проекта. Действия применяются к выделенным строкам.
 * ================================================================
 */

var MA_SITE_ADMIN_URL = 'https://avatar-manual.pages.dev/__admin';
var MA_HEADER_ROW = 2;              // строка с заголовками колонок
var MA_LOGIN_HEADER = 'Логин';      // колонка, где заголовок начинается с этого слова
var MA_NAME_HEADER = 'ФИО';
var MA_BLOCKED_MARK = 'ЗАБЛОКИРОВАН: ';
var MA_KEY_PROPERTY = 'MANUAL_ADMIN_KEY';
var MA_EMAIL_HEADER = 'Почта Tagme'; // куда отправлять логин
var MA_SITE_URL = 'https://avatar-manual.pages.dev/';
var MA_SESSION_DAYS = 30;           // как долго сайт помнит вход (задано в коде сайта)

function manualAccessAddMenu() {
  SpreadsheetApp.getUi().createMenu('Доступ к мануалу')
    .addItem('Выдать логин выделенным', 'manualAccessIssue')
    .addItem('Сбросить пароль выделенным', 'manualAccessReset')
    .addItem('Отправить логин на почту выделенным', 'manualAccessSendMail')
    .addSeparator()
    .addItem('Заблокировать выделенных', 'manualAccessBlock')
    .addItem('Разблокировать выделенных', 'manualAccessUnblock')
    .addSeparator()
    .addItem('Журнал за 7 дней', 'manualAccessLog7')
    .addItem('Журнал за 30 дней', 'manualAccessLog30')
    .addItem('Журнал за 180 дней', 'manualAccessLog180')
    .addSeparator()
    .addItem('Ввести секретный ключ', 'manualAccessSetKey')
    .addToUi();
}

function manualAccessLog7() { manualAccessLog_(7); }
function manualAccessLog30() { manualAccessLog_(30); }
function manualAccessLog180() { manualAccessLog_(180); }

var MA_LOG_SHEET = 'Журнал мануала';
var MA_EVENT_NAMES = {
  login_ok: 'Вход', login_fail: 'Неверный пароль', locked: 'Пауза после 5 неверных паролей',
  logout: 'Выход', view: 'Просмотр страницы', admin_add: 'Выдан логин', admin_reset: 'Сброшен пароль',
  admin_block: 'Заблокирован', admin_unblock: 'Разблокирован',
};

// Выгружает журнал сайта на лист «Журнал мануала» (лист каждый раз перезаписывается).
// ФИО подставляется по логину из колонки «Логин и пароль» основного листа.
function manualAccessLog_(days) {
  var ui = SpreadsheetApp.getUi();
  if (!PropertiesService.getScriptProperties().getProperty(MA_KEY_PROPERTY)) {
    ui.alert('Сначала: меню «Доступ к мануалу» → «Ввести секретный ключ».');
    return;
  }
  var res = manualAccessCall_({ action: 'log', days: days });
  if (res.error) { ui.alert('Журнал не получен: ' + res.error); return; }

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var names = manualAccessNames_(ss);
  var sheet = ss.getSheetByName(MA_LOG_SHEET) || ss.insertSheet(MA_LOG_SHEET);
  sheet.clear();
  var header = [['Время', 'Логин', 'ФИО', 'Событие', 'Страница']];
  var rows = res.events.map(function (e) {
    return [new Date(e.ts), e.login, names[String(e.login).toLowerCase()] || '',
      MA_EVENT_NAMES[e.kind] || e.kind, e.path ? decodeURIComponent(e.path) : ''];
  });
  sheet.getRange(1, 1, 1, 5).setValues(header).setFontWeight('bold');
  if (rows.length) {
    sheet.getRange(2, 1, rows.length, 5).setValues(rows);
    sheet.getRange(2, 1, rows.length, 1).setNumberFormat('dd.MM.yyyy HH:mm');
  }
  sheet.setFrozenRows(1);
  sheet.autoResizeColumns(1, 5);
  ss.setActiveSheet(sheet);
  ui.alert('Журнал за ' + days + ' дн.: ' + rows.length + ' записей' +
    (res.truncated ? ' (показаны только последние 50 000)' : '') + '. Лист «' + MA_LOG_SHEET + '».');
}

// Логин → ФИО по всем листам, где есть колонки «ФИО» и «Логин…».
function manualAccessNames_(ss) {
  var map = {};
  ss.getSheets().forEach(function (sh) {
    if (sh.getName() === MA_LOG_SHEET || sh.getLastRow() <= MA_HEADER_ROW) return;
    var cols = manualAccessColumns_(sh);
    if (!cols) return;
    var n = sh.getLastRow() - MA_HEADER_ROW;
    var nameVals = sh.getRange(MA_HEADER_ROW + 1, cols.name, n, 1).getValues();
    var loginVals = sh.getRange(MA_HEADER_ROW + 1, cols.login, n, 1).getValues();
    for (var i = 0; i < n; i++) {
      var login = manualAccessLogin_(String(loginVals[i][0]));
      if (login) map[login.toLowerCase()] = String(nameVals[i][0]).trim();
    }
  });
  return map;
}

function manualAccessSetKey() {
  var ui = SpreadsheetApp.getUi();
  var r = ui.prompt('Секретный ключ', 'Вставьте ключ управления логинами (он хранится в настройках скрипта, не в ячейках).', ui.ButtonSet.OK_CANCEL);
  if (r.getSelectedButton() !== ui.Button.OK) return;
  var key = r.getResponseText().trim();
  if (key.length < 32) { ui.alert('Ключ слишком короткий — проверьте, что вставили его целиком.'); return; }
  PropertiesService.getScriptProperties().setProperty(MA_KEY_PROPERTY, key);
  var check = manualAccessCall_({ action: 'list' });
  ui.alert(check.error ? 'Ключ сохранён, но сайт ответил: ' + check.error : 'Ключ сохранён и работает.');
}

function manualAccessIssue() {
  manualAccessForRows_('Выдать логин', function (cell, current) {
    var existing = manualAccessLogin_(current);
    if (existing) return 'уже есть логин ' + existing + ' — пропущено';
    var res = manualAccessCall_({ action: 'add' });
    if (res.error) return 'ошибка: ' + res.error;
    cell.setValue('логин ' + res.login + ', пароль ' + res.password);
    return 'выдан ' + res.login;
  });
}

function manualAccessReset() {
  if (!manualAccessConfirm_('Сбросить пароль выделенным? Старые пароли перестанут работать, асессоров выкинет с сайта.')) return;
  manualAccessForRows_('Сбросить пароль', function (cell, current) {
    var login = manualAccessLogin_(current);
    if (!login) return 'нет логина — пропущено';
    var res = manualAccessCall_({ action: 'reset', login: login });
    if (res.error) return 'ошибка: ' + res.error;
    var blocked = current.indexOf(MA_BLOCKED_MARK) === 0 ? MA_BLOCKED_MARK : '';
    cell.setValue(blocked + 'логин ' + res.login + ', пароль ' + res.password);
    return 'новый пароль для ' + res.login;
  });
}

function manualAccessBlock() {
  if (!manualAccessConfirm_('Заблокировать выделенных? Доступ к сайту закроется сразу.')) return;
  manualAccessForRows_('Заблокировать', function (cell, current) {
    var login = manualAccessLogin_(current);
    if (!login) return 'нет логина — пропущено';
    var res = manualAccessCall_({ action: 'block', login: login });
    if (res.error) return 'ошибка: ' + res.error;
    if (current.indexOf(MA_BLOCKED_MARK) !== 0) cell.setValue(MA_BLOCKED_MARK + current);
    return login + ' заблокирован';
  });
}

function manualAccessUnblock() {
  manualAccessForRows_('Разблокировать', function (cell, current) {
    var login = manualAccessLogin_(current);
    if (!login) return 'нет логина — пропущено';
    var res = manualAccessCall_({ action: 'unblock', login: login });
    if (res.error) return 'ошибка: ' + res.error;
    if (current.indexOf(MA_BLOCKED_MARK) === 0) cell.setValue(current.slice(MA_BLOCKED_MARK.length));
    return login + ' разблокирован';
  });
}

// Письмо с логином и паролем на почту из колонки «Почта Tagme».
// Заблокированных и строки без логина или почты пропускает. После отправки ставит
// на ячейку с логином примечание «Отправлено на почту ...».
function manualAccessSendMail() {
  var ui = SpreadsheetApp.getUi();
  var sheet = SpreadsheetApp.getActiveSheet();
  var cols = manualAccessColumns_(sheet);
  var emailCol = manualAccessColumn_(sheet, MA_EMAIL_HEADER);
  if (!cols || !emailCol) {
    ui.alert('Не нашла колонки «' + MA_NAME_HEADER + '», «' + MA_LOGIN_HEADER + '…» и «' + MA_EMAIL_HEADER + '» в строке ' + MA_HEADER_ROW + ' на этом листе.');
    return;
  }
  var rows = manualAccessRows_(sheet);
  if (rows.length === 0) { ui.alert('Выделите строки асессоров (ниже строки заголовков).'); return; }

  var toSend = [], skipped = [];
  rows.forEach(function (row) {
    var name = String(sheet.getRange(row, cols.name).getValue()).trim() || ('строка ' + row);
    var cell = sheet.getRange(row, cols.login);
    var text = String(cell.getValue()).trim();
    var email = String(sheet.getRange(row, emailCol).getValue()).trim();
    var login = manualAccessLogin_(text);
    var pw = /пароль\s+(\S+)/i.exec(text);
    if (text.indexOf(MA_BLOCKED_MARK) === 0) skipped.push(name + ': заблокирован, пропущено');
    else if (!login || !pw) skipped.push(name + ': нет логина и пароля, сначала «Выдать логин»');
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) skipped.push(name + ': нет почты в колонке «' + MA_EMAIL_HEADER + '»');
    else toSend.push({ name: name, email: email, login: login, password: pw[1].replace(/[,;.]+$/, ''), cell: cell });
  });

  if (toSend.length === 0) { ui.alert('Отправить некому', skipped.join('\n'), ui.ButtonSet.OK); return; }
  var list = toSend.map(function (p) { return p.name + ' → ' + p.email + ' (' + p.login + ')'; }).join('\n');
  if (!manualAccessConfirm_('Отправить письмо с логином и паролем?\n\n' + list +
      (skipped.length ? '\n\nНе отправим:\n' + skipped.join('\n') : ''))) return;

  var stamp = Utilities.formatDate(new Date(), 'Europe/Moscow', 'dd.MM.yyyy HH:mm');
  var report = toSend.map(function (p) {
    try {
      MailApp.sendEmail({ to: p.email, subject: 'Доступ к сайту-мануалу проекта «Аватар»', body: manualAccessMailText_(p) });
      p.cell.setNote('Отправлено на почту ' + p.email + ' ' + stamp);
      return p.name + ': отправлено на ' + p.email;
    } catch (e) {
      return p.name + ': не отправлено (' + e.message + ')';
    }
  });
  ui.alert('Отправка логинов', report.concat(skipped).join('\n') +
    '\n\nОсталось писем на сегодня: ' + MailApp.getRemainingDailyQuota(), ui.ButtonSet.OK);
}

function manualAccessMailText_(p) {
  return [
    'Здравствуйте, ' + p.name + '!',
    '',
    'Ваш доступ к сайту-мануалу проекта «Аватар».',
    '',
    'Адрес сайта: ' + MA_SITE_URL,
    'Логин: ' + p.login,
    'Пароль: ' + p.password,
    '',
    'Логин и пароль личные, не передавайте их никому.',
    '',
    'После входа сайт запоминает вас на ' + MA_SESSION_DAYS + ' дней. Когда срок пройдёт, сайт сам попросит войти ещё раз: введите эти же логин и пароль. Новый пароль запрашивать не нужно.',
    '',
    'Если пароль потерялся или не подходит, напишите менеджеру проекта, вам выдадут новый.',
    '',
    'Это письмо отправлено автоматически.',
  ].join('\n');
}

// --- служебное (имена с «_» в конце в меню не видны) -------------------------------------------

function manualAccessForRows_(title, fn) {
  var ui = SpreadsheetApp.getUi();
  var sheet = SpreadsheetApp.getActiveSheet();
  var cols = manualAccessColumns_(sheet);
  if (!cols) {
    ui.alert('Не нашла колонки «' + MA_NAME_HEADER + '» и «' + MA_LOGIN_HEADER + '…» в строке ' + MA_HEADER_ROW + ' на этом листе.');
    return;
  }
  if (!PropertiesService.getScriptProperties().getProperty(MA_KEY_PROPERTY)) {
    ui.alert('Сначала: меню «Доступ к мануалу» → «Ввести секретный ключ».');
    return;
  }
  var rows = manualAccessRows_(sheet);
  if (rows.length === 0) { ui.alert('Выделите строки асессоров (ниже строки заголовков).'); return; }
  var report = [];
  rows.forEach(function (row) {
    var name = String(sheet.getRange(row, cols.name).getValue()).trim() || ('строка ' + row);
    var cell = sheet.getRange(row, cols.login);
    report.push(name + ': ' + fn(cell, String(cell.getValue()).trim()));
  });
  ui.alert(title, report.join('\n'), ui.ButtonSet.OK);
}

function manualAccessColumns_(sheet) {
  var headers = sheet.getRange(MA_HEADER_ROW, 1, 1, sheet.getLastColumn()).getValues()[0];
  var name = 0, login = 0;
  headers.forEach(function (h, i) {
    var t = String(h).trim();
    if (!name && t.indexOf(MA_NAME_HEADER) === 0) name = i + 1;
    if (!login && t.indexOf(MA_LOGIN_HEADER) === 0) login = i + 1;
  });
  return name && login ? { name: name, login: login } : null;
}

function manualAccessColumn_(sheet, title) {
  var headers = sheet.getRange(MA_HEADER_ROW, 1, 1, sheet.getLastColumn()).getValues()[0];
  for (var i = 0; i < headers.length; i++) {
    if (String(headers[i]).replace(/\s+/g, ' ').trim().indexOf(title) === 0) return i + 1;
  }
  return 0;
}

function manualAccessRows_(sheet) {
  var seen = {}, rows = [];
  var list = sheet.getActiveRangeList();
  (list ? list.getRanges() : [sheet.getActiveRange()]).forEach(function (r) {
    for (var row = r.getRow(); row < r.getRow() + r.getNumRows(); row++) {
      if (row > MA_HEADER_ROW && !seen[row] && !sheet.isRowHiddenByFilter(row)) { seen[row] = true; rows.push(row); }
    }
  });
  return rows;
}

function manualAccessLogin_(text) {
  var m = /\b(Assessor\d+|Admin\d+)\b/i.exec(text || '');
  return m ? m[1] : '';
}

function manualAccessConfirm_(text) {
  var ui = SpreadsheetApp.getUi();
  return ui.alert('Подтвердите', text, ui.ButtonSet.YES_NO) === ui.Button.YES;
}

function manualAccessCall_(payload) {
  var key = PropertiesService.getScriptProperties().getProperty(MA_KEY_PROPERTY);
  try {
    var res = UrlFetchApp.fetch(MA_SITE_ADMIN_URL, {
      method: 'post',
      contentType: 'application/json',
      headers: { Authorization: 'Bearer ' + key },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true,
      followRedirects: false,
    });
    var data = {};
    try { data = JSON.parse(res.getContentText()); } catch (e) { data = { error: 'сайт ответил ' + res.getResponseCode() }; }
    if (res.getResponseCode() >= 400 && !data.error) data.error = 'сайт ответил ' + res.getResponseCode();
    return data;
  } catch (e) {
    return { error: 'нет связи с сайтом (' + e.message + ')' };
  }
}

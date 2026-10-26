/**
 * Меню «Доступ к мануалу» в Google-таблице со списком асессоров.
 * Выдаёт, сбрасывает, блокирует и разблокирует логины сайта-мануала (Assessor1, Assessor2...).
 *
 * Как поставить: Расширения → Apps Script → вставить этот код вместо пустого → Сохранить.
 * Обновить таблицу, в меню «Доступ к мануалу» → «Ввести секретный ключ» (ключ один раз).
 *
 * В сайт уходит только логин вида Assessor7 — ФИО и почты из таблицы никуда не передаются.
 * Действия применяются к строкам, выделенным мышкой (можно несколько строк сразу).
 */

var SITE_ADMIN_URL = 'https://avatar-manual.pages.dev/__admin';
var HEADER_ROW = 2;              // строка с заголовками колонок
var LOGIN_HEADER = 'Логин';      // колонка, где заголовок начинается с этого слова
var NAME_HEADER = 'ФИО';
var BLOCKED_MARK = 'ЗАБЛОКИРОВАН: ';
var KEY_PROPERTY = 'MANUAL_ADMIN_KEY';

function onOpen() {
  SpreadsheetApp.getUi().createMenu('Доступ к мануалу')
    .addItem('Выдать логин выделенным', 'issueLogins')
    .addItem('Сбросить пароль выделенным', 'resetPasswords')
    .addSeparator()
    .addItem('Заблокировать выделенных', 'blockSelected')
    .addItem('Разблокировать выделенных', 'unblockSelected')
    .addSeparator()
    .addItem('Ввести секретный ключ', 'setKey')
    .addToUi();
}

function setKey() {
  var ui = SpreadsheetApp.getUi();
  var r = ui.prompt('Секретный ключ', 'Вставьте ключ управления логинами (он хранится в настройках скрипта, не в ячейках).', ui.ButtonSet.OK_CANCEL);
  if (r.getSelectedButton() !== ui.Button.OK) return;
  var key = r.getResponseText().trim();
  if (key.length < 32) { ui.alert('Ключ слишком короткий — проверьте, что вставили его целиком.'); return; }
  PropertiesService.getScriptProperties().setProperty(KEY_PROPERTY, key);
  var check = callSite_({ action: 'list' });
  ui.alert(check.error ? 'Ключ сохранён, но сайт ответил: ' + check.error : 'Ключ сохранён и работает.');
}

function issueLogins() {
  forSelectedRows_('Выдать логин', function (row, cell, current) {
    if (loginFrom_(current)) return 'уже есть логин ' + loginFrom_(current) + ' — пропущено';
    var res = callSite_({ action: 'add' });
    if (res.error) return 'ошибка: ' + res.error;
    cell.setValue('логин ' + res.login + ', пароль ' + res.password);
    return 'выдан ' + res.login;
  });
}

function resetPasswords() {
  if (!confirm_('Сбросить пароль выделенным? Старые пароли перестанут работать, асессоров выкинет с сайта.')) return;
  forSelectedRows_('Сбросить пароль', function (row, cell, current) {
    var login = loginFrom_(current);
    if (!login) return 'нет логина — пропущено';
    var res = callSite_({ action: 'reset', login: login });
    if (res.error) return 'ошибка: ' + res.error;
    var blocked = current.indexOf(BLOCKED_MARK) === 0 ? BLOCKED_MARK : '';
    cell.setValue(blocked + 'логин ' + res.login + ', пароль ' + res.password);
    return 'новый пароль для ' + res.login;
  });
}

function blockSelected() {
  if (!confirm_('Заблокировать выделенных? Доступ к сайту закроется сразу.')) return;
  forSelectedRows_('Заблокировать', function (row, cell, current) {
    var login = loginFrom_(current);
    if (!login) return 'нет логина — пропущено';
    var res = callSite_({ action: 'block', login: login });
    if (res.error) return 'ошибка: ' + res.error;
    if (current.indexOf(BLOCKED_MARK) !== 0) cell.setValue(BLOCKED_MARK + current);
    return login + ' заблокирован';
  });
}

function unblockSelected() {
  forSelectedRows_('Разблокировать', function (row, cell, current) {
    var login = loginFrom_(current);
    if (!login) return 'нет логина — пропущено';
    var res = callSite_({ action: 'unblock', login: login });
    if (res.error) return 'ошибка: ' + res.error;
    if (current.indexOf(BLOCKED_MARK) === 0) cell.setValue(current.slice(BLOCKED_MARK.length));
    return login + ' разблокирован';
  });
}

// --- служебное ---------------------------------------------------------------------------------

function forSelectedRows_(title, fn) {
  var ui = SpreadsheetApp.getUi();
  var sheet = SpreadsheetApp.getActiveSheet();
  var cols = findColumns_(sheet);
  if (!cols) {
    ui.alert('Не нашла колонки «' + NAME_HEADER + '» и «' + LOGIN_HEADER + '…» в строке ' + HEADER_ROW + '.');
    return;
  }
  if (!PropertiesService.getScriptProperties().getProperty(KEY_PROPERTY)) {
    ui.alert('Сначала: меню «Доступ к мануалу» → «Ввести секретный ключ».');
    return;
  }
  var rows = selectedRows_(sheet);
  if (rows.length === 0) { ui.alert('Выделите строки асессоров (ниже строки заголовков).'); return; }
  var report = [];
  rows.forEach(function (row) {
    var name = String(sheet.getRange(row, cols.name).getValue()).trim() || ('строка ' + row);
    var cell = sheet.getRange(row, cols.login);
    report.push(name + ': ' + fn(row, cell, String(cell.getValue()).trim()));
  });
  ui.alert(title, report.join('\n'), ui.ButtonSet.OK);
}

function findColumns_(sheet) {
  var headers = sheet.getRange(HEADER_ROW, 1, 1, sheet.getLastColumn()).getValues()[0];
  var name = 0, login = 0;
  headers.forEach(function (h, i) {
    var t = String(h).trim();
    if (!name && t.indexOf(NAME_HEADER) === 0) name = i + 1;
    if (!login && t.indexOf(LOGIN_HEADER) === 0) login = i + 1;
  });
  return name && login ? { name: name, login: login } : null;
}

function selectedRows_(sheet) {
  var seen = {}, rows = [];
  var list = sheet.getActiveRangeList();
  (list ? list.getRanges() : [sheet.getActiveRange()]).forEach(function (r) {
    for (var row = r.getRow(); row < r.getRow() + r.getNumRows(); row++) {
      if (row > HEADER_ROW && !seen[row] && !sheet.isRowHiddenByFilter(row)) { seen[row] = true; rows.push(row); }
    }
  });
  return rows;
}

function loginFrom_(text) {
  var m = /\b(Assessor\d+|Admin\d+)\b/i.exec(text || '');
  return m ? m[1] : '';
}

function confirm_(text) {
  var ui = SpreadsheetApp.getUi();
  return ui.alert('Подтвердите', text, ui.ButtonSet.YES_NO) === ui.Button.YES;
}

function callSite_(payload) {
  var key = PropertiesService.getScriptProperties().getProperty(KEY_PROPERTY);
  try {
    var res = UrlFetchApp.fetch(SITE_ADMIN_URL, {
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

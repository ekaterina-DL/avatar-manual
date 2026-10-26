-- База входа на сайт (Cloudflare D1, имя manual-auth, привязка DB).
-- Почт и имён здесь нет: только условные логины (Assessor1, Assessor2...).

CREATE TABLE IF NOT EXISTS users (
  login        TEXT PRIMARY KEY COLLATE NOCASE,
  pw           TEXT NOT NULL,              -- pbkdf2$<итерации>$<соль>$<хэш>, сам пароль не хранится
  groups       TEXT NOT NULL DEFAULT 'stage2',
  active       INTEGER NOT NULL DEFAULT 1, -- 0 = заблокирован
  sv           INTEGER NOT NULL DEFAULT 1, -- версия сеанса: +1 выкидывает все открытые входы
  fails        INTEGER NOT NULL DEFAULT 0,
  locked_until INTEGER NOT NULL DEFAULT 0, -- мс; блокировка после серии неверных паролей
  created      INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  id    INTEGER PRIMARY KEY AUTOINCREMENT,
  ts    INTEGER NOT NULL,
  login TEXT NOT NULL,
  kind  TEXT NOT NULL,                     -- login_ok, login_fail, locked, logout, view
  path  TEXT
);

CREATE INDEX IF NOT EXISTS events_ts ON events (ts);

// Конфиг тестирования. Значения безопасно держать в открытом виде: endpoint веб-приложения
// Apps Script всё равно виден в исходниках страницы. token — лёгкая защита от случайных
// посторонних отправок, не секрет.
window.QUIZ_CONFIG = {
  // URL веб-приложения Google Apps Script (см. docs/quiz-apps-script.md).
  endpoint: "https://script.google.com/macros/s/AKfycbwt2CIoLUBjsGA8VyeiQRqNMgL0OcxD5szM_2vuG902R3UN1wr0pe3r26lFhtN--O_y/exec",
  // Тот же токен, что зашит в apps-script.gs (константа TOKEN).
  token: "avatar-stage2-quiz",
  // Порог вердикта «Сдано», проценты.
  passPercent: 80
};

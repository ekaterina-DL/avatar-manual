/* Самопроверка по 2 этапу. Ванильный JS, активируется только на странице с #quiz-root.
   Данные вопросов — в <script id="quiz-bank">, конфиг — window.QUIZ_CONFIG. */
(function () {
  "use strict";

  var root = document.getElementById("quiz-root");
  if (!root) return;

  var CFG = window.QUIZ_CONFIG || { endpoint: "", token: "", passPercent: 80 };
  var LS_KEY = "avatar-quiz:last-ids";
  var QUESTION_SECONDS = 60;
  var TOTAL = 15;
  var TOPIC_CAP = 6;

  var PLAN = [
    { cat: "A", target: 5, min: 3 },
    { cat: "B", target: 3, min: 2 },
    { cat: "C", target: 2, min: 1 },
    { cat: "DE", target: 2, min: 1 },
    { cat: "F", target: 3, min: 2 }
  ];

  var bank = readBank();
  var state = null;

  function readBank() {
    var el = document.getElementById("quiz-bank");
    if (!el) return { questions: [] };
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return { questions: [] };
    }
  }

  function shuffle(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i];
      a[i] = a[j];
      a[j] = t;
    }
    return a;
  }

  function pickN(arr, n) {
    return shuffle(arr).slice(0, n);
  }

  function readExcludeIds() {
    try {
      var v = JSON.parse(localStorage.getItem(LS_KEY) || "[]");
      return Array.isArray(v) ? v : [];
    } catch (e) {
      return [];
    }
  }

  function assembleSet(allQuestions, excludeIds) {
    excludeIds = excludeIds || [];
    var exclude = {};
    excludeIds.forEach(function (id) { exclude[id] = true; });

    var byCat = {};
    allQuestions.forEach(function (q) {
      (byCat[q.category] = byCat[q.category] || []).push(q);
    });

    var chosen = [];
    var topicCount = {};

    function canAdd(q) {
      if (chosen.indexOf(q) !== -1) return false;
      var tc = topicCount[q.topic] || 0;
      return tc < TOPIC_CAP;
    }
    function add(q) {
      chosen.push(q);
      topicCount[q.topic] = (topicCount[q.topic] || 0) + 1;
    }

    // 1-й проход: по плану, сначала без исключённых id
    PLAN.forEach(function (row) {
      var pool = (byCat[row.cat] || []);
      var fresh = shuffle(pool.filter(function (q) { return !exclude[q.id] && canAdd(q); }));
      var stale = shuffle(pool.filter(function (q) { return exclude[q.id] && canAdd(q); }));
      var ordered = fresh.concat(stale);
      var added = 0;
      for (var i = 0; i < ordered.length && added < row.target; i++) {
        if (canAdd(ordered[i])) { add(ordered[i]); added++; }
      }
    });

    // 2-й проход: добор до TOTAL из всего пула (свежие раньше исключённых)
    if (chosen.length < TOTAL) {
      var restFresh = shuffle(allQuestions.filter(function (q) { return !exclude[q.id] && canAdd(q); }));
      var restStale = shuffle(allQuestions.filter(function (q) { return exclude[q.id] && canAdd(q); }));
      var rest = restFresh.concat(restStale);
      for (var k = 0; k < rest.length && chosen.length < TOTAL; k++) {
        if (canAdd(rest[k])) add(rest[k]);
      }
    }

    // если и теперь мало (крошечный банк) — снимаем потолок по topic
    if (chosen.length < TOTAL) {
      var any = shuffle(allQuestions.filter(function (q) { return chosen.indexOf(q) === -1; }));
      for (var z = 0; z < any.length && chosen.length < TOTAL; z++) chosen.push(any[z]);
    }

    return shuffle(chosen).slice(0, TOTAL);
  }

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    attrs = attrs || {};
    Object.keys(attrs).forEach(function (k) {
      if (k === "class") node.className = attrs[k];
      else if (k === "text") node.textContent = attrs[k];
      else if (k === "html") node.innerHTML = attrs[k];
      else node.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) {
      node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return node;
  }

  function renderStart() {
    root.innerHTML = "";
    var wrap = el("div", { class: "quiz-card quiz-start" });

    if (!bank.questions || bank.questions.length < TOTAL) {
      wrap.appendChild(el("p", {
        class: "quiz-warn",
        text: "Банк вопросов сейчас недоступен или слишком мал. Обновите страницу позже."
      }));
      root.appendChild(wrap);
      return;
    }

    wrap.appendChild(el("h2", { text: "Начать тестирование" }));
    wrap.appendChild(el("p", {
      text: "Введите фамилию и имя — результат будет сохранён. 15 вопросов, по 60 секунд на каждый."
    }));

    var form = el("form", { class: "quiz-fio" });
    var iSurname = el("input", { type: "text", name: "surname", placeholder: "Фамилия", autocomplete: "family-name" });
    var iName = el("input", { type: "text", name: "name", placeholder: "Имя", autocomplete: "given-name" });
    var btn = el("button", { type: "submit", class: "quiz-btn", disabled: "disabled", text: "Начать тест" });

    function sync() {
      var ok = iSurname.value.trim() && iName.value.trim();
      if (ok) btn.removeAttribute("disabled");
      else btn.setAttribute("disabled", "disabled");
    }
    iSurname.addEventListener("input", sync);
    iName.addEventListener("input", sync);
    sync();

    form.appendChild(iSurname);
    form.appendChild(iName);
    form.appendChild(btn);
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (!iSurname.value.trim() || !iName.value.trim()) return;
      startQuiz(iSurname.value.trim(), iName.value.trim());
    });

    wrap.appendChild(form);
    root.appendChild(wrap);
  }

  function startQuiz(surname, name) {
    var set = assembleSet(bank.questions, readExcludeIds());
    state = {
      surname: surname,
      name: name,
      set: set,
      idx: 0,
      answers: [],
      startedAt: Date.now()
    };
    renderQuestion();
  }

  // Заглушка — полноценно реализуется в Задаче 10.
  function renderQuestion() {
    root.innerHTML = "";
    var q = state.set[state.idx];
    var card = el("div", { class: "quiz-card" });
    card.appendChild(el("div", { class: "quiz-progress", text: "Вопрос " + (state.idx + 1) + " / " + TOTAL }));
    card.appendChild(el("p", { class: "quiz-question", text: q.question }));
    card.appendChild(el("pre", { text: JSON.stringify(q.options, null, 2) }));
    root.appendChild(card);
  }

  function renderResults() {} // Задача 11
  function submitResults() {}  // Задача 12

  // экспорт для отладки из консоли
  window.__quiz = { assembleSet: assembleSet, readBank: readBank, get state() { return state; } };

  renderStart();
})();

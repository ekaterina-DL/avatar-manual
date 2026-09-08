/* Самопроверка по 2 этапу. Ванильный JS, активируется только на странице с #quiz-root.
   Данные вопросов — в <script id="quiz-bank">, конфиг — window.QUIZ_CONFIG. */
(function () {
  "use strict";

  // Плашка на пункте «Тестирование» в левом меню (оформление — в quiz.css). Ставим её на
  // всех страницах: на самой странице теста активный пункт имеет href="./", по атрибуту
  // href такой не поймать, поэтому сверяемся с уже разрешённым абсолютным URL ссылки.
  var navLinks = document.querySelectorAll(".md-nav__link");
  for (var n = 0; n < navLinks.length; n++) {
    if (/\/manual-2-etap\/07-testirovanie\/$/.test(navLinks[n].href || "")) {
      navLinks[n].classList.add("quiz-nav-link");
    }
  }

  var root = document.getElementById("quiz-root");
  if (!root) return;

  var CFG = window.QUIZ_CONFIG || { endpoint: "", token: "", passPercent: 90 };
  var LS_KEY = "avatar-quiz:last-ids";
  var QUESTION_SECONDS = 60;
  var TOTAL = 20;
  var TOPIC_CAP = 6;

  var PLAN = [
    { cat: "A", target: 6 },
    { cat: "B", target: 4 },
    { cat: "C", target: 3 },
    { cat: "DE", target: 2 },
    { cat: "F", target: 5 }
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
      text: "Введите фамилию и имя — результат будет сохранён. 20 вопросов, по 60 секунд на каждый."
    }));

    var form = el("form", { class: "quiz-fio" });
    var iSurname = el("input", { type: "text", name: "surname", placeholder: "Фамилия", "aria-label": "Фамилия", autocomplete: "family-name" });
    var iName = el("input", { type: "text", name: "name", placeholder: "Имя", "aria-label": "Имя", autocomplete: "given-name" });
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
    _sent = false; // сброс защиты от повторной отправки — это новая попытка
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

  function ytId(url) {
    var m = url.match(/(?:youtube\.com\/(?:shorts\/|watch\?v=)|youtu\.be\/)([A-Za-z0-9_-]+)/);
    return m ? m[1] : "";
  }
  function vkIds(url) {
    var m = url.match(/video(-?\d+)_(\d+)/);
    return m ? { oid: m[1], id: m[2] } : null;
  }

  function buildMedia(q, onReady) {
    if (!q.videoUrl) {
      setTimeout(onReady, 0);
      return null;
    }
    var box = el("div", { class: "quiz-media" });
    if (q.videoKind === "mp4") {
      // Медиа-фрагмент #t=начало[,конец] — плеер стартует и (в Chrome вместе с loop)
      // крутится в пределах оцениваемого сегмента.
      var frag = "";
      if (q.videoStart != null || q.videoEnd != null) {
        frag = "#t=" + (q.videoStart != null ? q.videoStart : 0) +
               (q.videoEnd != null ? "," + q.videoEnd : "");
      }
      var v = el("video", {
        src: q.videoUrl + frag,
        controls: "controls",
        muted: "muted",
        loop: "loop",
        playsinline: "playsinline",
        preload: "auto"
      });
      v.muted = true;
      var fired = false;
      var ready = function () { if (!fired) { fired = true; onReady(); } };
      v.addEventListener("loadeddata", ready);
      v.addEventListener("error", ready);
      setTimeout(ready, 8000);
      v.addEventListener("canplay", function () { v.play().catch(function () {}); });
      box.appendChild(v);
    } else {
      var src = "";
      if (q.videoKind === "youtube") {
        src = "https://www.youtube-nocookie.com/embed/" + ytId(q.videoUrl);
      } else {
        var ids = vkIds(q.videoUrl);
        src = ids ? "https://vk.com/video_ext.php?oid=" + ids.oid + "&id=" + ids.id + "&hd=2" : q.videoUrl;
      }
      box.appendChild(el("iframe", {
        class: "quiz-embed",
        src: src,
        loading: "eager",
        allow: "autoplay; encrypted-media; picture-in-picture",
        allowfullscreen: "allowfullscreen"
      }));
      setTimeout(onReady, 4000);
    }
    return box;
  }

  function Timer(seconds, onTick, onExpire) {
    var total = seconds * 1000;
    var end = 0;
    var raf = 0;
    var stopped = false;
    function frame() {
      if (stopped) return;
      var left = Math.max(0, end - Date.now());
      onTick(left / 1000, left / total);
      if (left <= 0) { stopped = true; onExpire(); return; }
      raf = requestAnimationFrame(frame);
    }
    return {
      start: function () { end = Date.now() + total; stopped = false; raf = requestAnimationFrame(frame); },
      stop: function () { stopped = true; if (raf) cancelAnimationFrame(raf); }
    };
  }

  function timerRing() {
    var NS = "http://www.w3.org/2000/svg";
    var svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", "0 0 40 40");
    svg.setAttribute("class", "quiz-ring");
    var bg = document.createElementNS(NS, "circle");
    bg.setAttribute("cx", "20"); bg.setAttribute("cy", "20"); bg.setAttribute("r", "18");
    bg.setAttribute("class", "quiz-ring-bg");
    var fg = document.createElementNS(NS, "circle");
    fg.setAttribute("cx", "20"); fg.setAttribute("cy", "20"); fg.setAttribute("r", "18");
    fg.setAttribute("class", "quiz-ring-fg");
    var C = 2 * Math.PI * 18;
    fg.setAttribute("stroke-dasharray", String(C));
    fg.setAttribute("stroke-dashoffset", "0");
    var label = document.createElementNS(NS, "text");
    label.setAttribute("x", "20"); label.setAttribute("y", "24");
    label.setAttribute("text-anchor", "middle"); label.setAttribute("class", "quiz-ring-text");
    label.textContent = "60";
    svg.appendChild(bg); svg.appendChild(fg); svg.appendChild(label);
    return {
      node: svg,
      update: function (secLeft, frac) {
        fg.setAttribute("stroke-dashoffset", String(C * (1 - frac)));
        label.textContent = String(Math.ceil(secLeft));
        if (secLeft <= 10) svg.classList.add("warn");
        else svg.classList.remove("warn");
      }
    };
  }

  function renderQuestion() {
    root.innerHTML = "";
    var q = state.set[state.idx];
    var options = shuffle(q.options.map(function (text, i) {
      return { text: text, correct: i === q.answer };
    }));

    var card = el("div", { class: "quiz-card" });

    var head = el("div", { class: "quiz-qhead" });
    head.appendChild(el("div", { class: "quiz-progress", text: "Вопрос " + (state.idx + 1) + " / " + TOTAL }));
    var ring = timerRing();
    head.appendChild(ring.node);
    card.appendChild(head);

    card.appendChild(el("p", { class: "quiz-question", text: q.question }));

    var locked = false;
    var timer = Timer(QUESTION_SECONDS, function (secLeft, frac) {
      ring.update(secLeft, frac);
    }, function () {
      if (!locked) lockAnswer(null);
    });

    var media = buildMedia(q, function () {
      if (!locked) timer.start();
    });
    if (media) card.appendChild(media);

    var list = el("div", { class: "quiz-options" });
    var btns = [];
    options.forEach(function (opt) {
      var b = el("button", { type: "button", class: "quiz-option", text: opt.text });
      b.addEventListener("click", function () { if (!locked) lockAnswer(opt.text); });
      btns.push({ b: b, opt: opt });
      list.appendChild(b);
    });
    card.appendChild(list);

    var feedback = el("div", { class: "quiz-feedback", hidden: "hidden" });
    card.appendChild(feedback);

    var next = el("button", { type: "button", class: "quiz-btn quiz-next", hidden: "hidden",
      text: state.idx + 1 < TOTAL ? "Далее" : "Показать результат" });
    next.addEventListener("click", function () {
      state.idx += 1;
      if (state.idx < TOTAL) renderQuestion();
      else renderResults();
    });
    card.appendChild(next);

    root.appendChild(card);

    function lockAnswer(chosenText) {
      locked = true;
      timer.stop();
      var correctText = q.options[q.answer];
      var ok = chosenText === correctText;

      btns.forEach(function (x) {
        x.b.setAttribute("disabled", "disabled");
        if (x.opt.correct) x.b.classList.add("is-correct");
        if (x.opt.text === chosenText && !x.opt.correct) x.b.classList.add("is-wrong");
      });

      feedback.hidden = false;
      if (chosenText === null) {
        feedback.className = "quiz-feedback bad";
        feedback.textContent = "Время вышло. Правильный ответ отмечен зелёным.";
      } else if (ok) {
        feedback.className = "quiz-feedback good";
        feedback.textContent = "Верно!";
      } else {
        feedback.className = "quiz-feedback bad";
        feedback.textContent = "Неверно. Правильный ответ отмечен зелёным.";
      }

      state.answers.push({
        id: q.id,
        question: q.question,
        topic: q.topic,
        chosen: chosenText,
        correct: correctText,
        ok: ok,
        review: q.review
      });

      next.hidden = false;
      next.focus();
    }
  }

  function computeScore(answers) {
    var correct = answers.filter(function (a) { return a.ok; }).length;
    var percent = Math.round((correct / TOTAL) * 100);
    var verdict = percent >= (CFG.passPercent || 90) ? "Сдано" : "Не сдано";
    return { correct: correct, percent: percent, verdict: verdict };
  }

  function reviewLink(url) {
    // "04-classifier.md#anchor" -> "../04-classifier/#anchor"
    var parts = String(url).split("#");
    var file = parts[0].replace(/\.md$/, "");
    var anchor = parts[1] ? "#" + parts[1] : "";
    return "../" + file + "/" + anchor;
  }

  function topicBreakdown(answers) {
    var byTopic = {};
    answers.forEach(function (a) {
      if (a.ok) return;
      if (!byTopic[a.topic]) {
        byTopic[a.topic] = { topic: a.topic, misses: 0, reviewUrl: a.review.url, reviewTitle: a.review.title };
      }
      byTopic[a.topic].misses += 1;
    });
    return Object.keys(byTopic).map(function (k) { return byTopic[k]; })
      .sort(function (x, y) { return y.misses - x.misses; });
  }

  function persistLastIds() {
    try {
      localStorage.setItem(LS_KEY, JSON.stringify(state.set.map(function (q) { return q.id; })));
    } catch (e) { /* приватный режим — не критично */ }
  }

  function renderResults() {
    persistLastIds();
    var sc = computeScore(state.answers);
    var wrong = state.answers.filter(function (a) { return !a.ok; });
    var breakdown = topicBreakdown(state.answers);

    root.innerHTML = "";
    var card = el("div", { class: "quiz-card quiz-results" });

    card.appendChild(el("h2", { text: "Результат" }));
    var verdictCls = sc.verdict === "Сдано" ? "pass" : "fail";
    card.appendChild(el("div", { class: "quiz-verdict " + verdictCls, text: sc.verdict }));
    card.appendChild(el("p", {
      class: "quiz-score",
      text: sc.percent + "% — верных ответов " + sc.correct + " из " + TOTAL
    }));
    card.appendChild(el("p", { class: "quiz-fio-line", text: state.surname + " " + state.name }));

    if (breakdown.length) {
      card.appendChild(el("h3", { text: "Что повторить" }));
      var table = el("table", { class: "quiz-breakdown" });
      var thead = el("tr", {}, [
        el("th", { text: "Тема" }), el("th", { text: "Ошибок" }), el("th", { text: "Раздел" })
      ]);
      table.appendChild(el("thead", {}, [thead]));
      var tbody = el("tbody");
      breakdown.forEach(function (row) {
        var link = el("a", { href: reviewLink(row.reviewUrl), text: row.reviewTitle });
        tbody.appendChild(el("tr", {}, [
          el("td", { text: row.topic }),
          el("td", { text: String(row.misses) }),
          el("td", {}, [link])
        ]));
      });
      table.appendChild(tbody);
      card.appendChild(table);
    } else {
      card.appendChild(el("p", { class: "quiz-feedback good", text: "Ошибок нет — повторять нечего." }));
    }

    if (wrong.length) {
      card.appendChild(el("h3", { text: "Разбор неверных ответов" }));
      var ul = el("ul", { class: "quiz-wrong-list" });
      wrong.forEach(function (a) {
        var li = el("li");
        li.appendChild(el("div", { class: "quiz-wrong-q", text: a.question }));
        li.appendChild(el("div", {
          class: "quiz-wrong-a",
          text: "Ваш ответ: " + (a.chosen === null ? "— (не успели)" : a.chosen)
        }));
        li.appendChild(el("div", { class: "quiz-wrong-c", text: "Верно: " + a.correct }));
        ul.appendChild(li);
      });
      card.appendChild(ul);
    }

    var status = el("div", { class: "quiz-send-status", text: "Отправка результата…" });
    card.appendChild(status);

    var again = el("button", { type: "button", class: "quiz-btn", text: "Пройти заново" });
    again.addEventListener("click", function () { startQuiz(state.surname, state.name); });
    card.appendChild(again);

    root.appendChild(card);

    submitResults(sc, wrong, status);
  }

  function buildPayload(sc, wrong) {
    return {
      token: CFG.token || "",
      startedAt: new Date(state.startedAt).toISOString(),
      finishedAt: new Date().toISOString(),
      durationSec: Math.round((Date.now() - state.startedAt) / 1000),
      surname: state.surname,
      name: state.name,
      percent: sc.percent,
      correct: sc.correct,
      total: TOTAL,
      verdict: sc.verdict,
      wrongAnswers: wrong.map(function (a, i) {
        return {
          n: i + 1,
          question: a.question,
          chosen: a.chosen,
          correct: a.correct,
          topic: a.topic,
          reviewUrl: a.review.url
        };
      }),
      questionIds: state.set.map(function (q) { return q.id; }),
      userAgent: navigator.userAgent
    };
  }

  var _sent = false;
  function submitResults(sc, wrong, statusEl) {
    if (_sent) return;
    _sent = true;

    if (!CFG.endpoint) {
      statusEl.className = "quiz-send-status warn";
      statusEl.textContent = "Отправка результата не настроена. Сделайте скриншот этого экрана и пришлите куратору.";
      return;
    }

    // Apps Script отвечает HTTP 200 и на успех, и на ошибку (bad token, внутреннее
    // исключение) — поэтому «промис разрешился» ещё не значит «сохранилось». Читаем тело
    // ответа и смотрим на "ok":true / "ok":false / "error". Если тело недоступно
    // (CORS/редирект) — показываем осторожную формулировку «подтверждение не получено».
    fetch(CFG.endpoint, {
      method: "POST",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify(buildPayload(sc, wrong)),
      keepalive: true
    }).then(function (r) { return r.text().catch(function () { return ""; }); })
      .then(function (t) {
        if (t.indexOf('"ok":true') !== -1) {
          statusEl.className = "quiz-send-status ok";
          statusEl.textContent = "Результат отправлен.";
        } else if (t.indexOf('"ok":false') !== -1 || t.indexOf('"error"') !== -1) {
          statusEl.className = "quiz-send-status warn";
          statusEl.textContent = "Результат не сохранён (ошибка приёмника). Сделайте скриншот этого экрана и пришлите куратору.";
        } else {
          statusEl.className = "quiz-send-status warn";
          statusEl.textContent = "Результат отправлен, но подтверждение не получено. На всякий случай сделайте скриншот этого экрана.";
        }
      })
      .catch(function () {
        statusEl.className = "quiz-send-status warn";
        statusEl.textContent = "Не удалось отправить результат автоматически. Сделайте скриншот этого экрана и пришлите куратору.";
      });
  }

  // экспорт для отладки из консоли
  window.__quiz = { assembleSet: assembleSet, readBank: readBank, get state() { return state; } };

  renderStart();
})();

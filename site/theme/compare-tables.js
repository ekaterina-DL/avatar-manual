document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".md-typeset table").forEach(function (table) {
    var headers = table.querySelectorAll("thead th");
    if (headers.length === 2) {
      var first = headers[0].textContent.trim();
      var second = headers[1].textContent.trim();
      if (first === "Правильно" && second === "Неправильно") {
        table.classList.add("compare-table");
        var firstCol = table.querySelectorAll("tbody td:first-child");
        var secondCol = table.querySelectorAll("tbody td:last-child");
        firstCol.forEach(function (td) { td.classList.add("compare-ok"); });
        secondCol.forEach(function (td) { td.classList.add("compare-no"); });
      }
    }
  });
});

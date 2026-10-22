/* Public gallery: load D1-backed entries from the Worker API. */
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  function cell(text, className) {
    var td = document.createElement("td");
    if (className) td.className = className;
    td.textContent = text == null ? "" : String(text);
    return td;
  }

  function link(href, label) {
    var a = document.createElement("a");
    a.href = href;
    a.textContent = label;
    return a;
  }

  function filesCell(files, scheme) {
    var td = document.createElement("td");
    td.className = "nowrap";
    var pdf = files[scheme ? "scheme_pdf" : "paper_pdf"];
    var docx = files[scheme ? "scheme_docx" : "paper_docx"];
    if (pdf) td.appendChild(link(pdf, "PDF"));
    if (pdf && docx) td.appendChild(document.createTextNode(" / "));
    if (docx) td.appendChild(link(docx, "DOCX"));
    return td;
  }

  function formatDate(iso) {
    var date = new Date(iso);
    return isNaN(date.getTime()) ? iso : date.toLocaleString();
  }

  ready(function () {
    var table = document.getElementById("gallery-table");
    if (!table) return;
    var body = table.tBodies[0];
    var empty = document.getElementById("gallery-empty");
    var status = document.getElementById("gallery-status");

    function showError(message) {
      if (!status) return;
      status.textContent = message;
      status.hidden = false;
    }

    fetch("/api/gallery", { headers: { Accept: "application/json" } })
      .then(function (response) {
        if (response.status === 404) return { items: [] };
        if (!response.ok) throw new Error("gallery request failed");
        return response.json();
      })
      .then(function (data) {
        var items = (data && data.items) || [];
        body.textContent = "";
        items.forEach(function (item) {
          var row = document.createElement("tr");
          row.appendChild(cell(item.subject));
          row.appendChild(cell(item.seed));
          row.appendChild(cell(item.mode));
          row.appendChild(cell(item.computed_marks == null
            ? "0" : item.computed_marks));
          row.appendChild(cell(formatDate(item.created_at), "nowrap"));
          var expires = cell(formatDate(item.expires_at), "nowrap");
          expires.title = "in " + item.expires_in_days + " day(s)";
          row.appendChild(expires);
          row.appendChild(cell(item.id, "mono"));
          row.appendChild(filesCell(item.files, false));
          row.appendChild(filesCell(item.files, true));
          body.appendChild(row);
        });
        table.hidden = items.length === 0;
        if (empty) empty.hidden = items.length !== 0;
      })
      .catch(function () {
        // Local development has no gallery API; keep the empty state.
        table.hidden = true;
        if (empty) empty.hidden = false;
        if (window.location.hostname !== "127.0.0.1" &&
            window.location.hostname !== "localhost") {
          showError("Could not load the public gallery.");
        }
      });
  });
})();

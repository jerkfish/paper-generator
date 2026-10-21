/* Library table: click a column title to sort; filter locally. */
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  ready(function () {
    var table = document.getElementById("library-table");
    if (!table || !table.tBodies.length) return;
    var tbody = table.tBodies[0];
    var rows = Array.prototype.slice.call(tbody.rows);
    var form = document.getElementById("library-filter");
    var count = document.getElementById("library-count");
    var sortKey = null;
    var sortDir = 1;

    function rowValue(row, key) {
      return row.getAttribute("data-" + key) || "";
    }

    function setIndicators() {
      table.querySelectorAll("th[data-sort]").forEach(function (th) {
        var active = th.getAttribute("data-sort") === sortKey;
        th.setAttribute("aria-sort",
          active ? (sortDir > 0 ? "ascending" : "descending") : "none");
        var mark = th.querySelector(".sort-mark");
        if (mark) mark.textContent = active ? (sortDir > 0 ? " ▲" : " ▼") : "";
      });
    }

    function sortBy(key, type) {
      if (sortKey === key) {
        sortDir = -sortDir;
      } else {
        sortKey = key;
        sortDir = 1;
      }
      rows.sort(function (a, b) {
        var av = rowValue(a, key);
        var bv = rowValue(b, key);
        var cmp;
        if (type === "number") {
          cmp = (parseFloat(av) || 0) - (parseFloat(bv) || 0);
        } else {
          cmp = av.localeCompare(bv, undefined,
            { numeric: true, sensitivity: "base" });
        }
        return cmp * sortDir;
      });
      rows.forEach(function (row) { tbody.appendChild(row); });
      setIndicators();
    }

    table.querySelectorAll("button.sort").forEach(function (button) {
      button.addEventListener("click", function () {
        sortBy(button.getAttribute("data-sort"),
          button.getAttribute("data-type") || "text");
      });
    });

    function value(id) {
      var el = document.getElementById(id);
      return el ? el.value : "any";
    }

    function updateQuery(params) {
      if (!window.history || !window.history.replaceState) return;
      var query = params.toString();
      var url = window.location.pathname + (query ? "?" + query : "");
      window.history.replaceState(null, "", url);
    }

    function applyFilters() {
      if (!form) return;
      var q = (value("q") || "").toLowerCase();
      var computed = value("computed");
      var topic = value("topic");
      var placeholders = value("placeholders");
      var shown = 0;

      rows.forEach(function (row) {
        var ok = true;
        var text = (row.getAttribute("data-text") || "").toLowerCase();
        var topics = "|" + (row.getAttribute("data-topics") || "") + "|";
        if (q && text.indexOf(q) === -1) ok = false;
        if (computed !== "any" &&
            row.getAttribute("data-computed") !== computed) ok = false;
        if (topic !== "any" && topics.indexOf("|" + topic + "|") === -1) ok = false;
        var ph = parseInt(row.getAttribute("data-placeholders") || "0", 10);
        if (placeholders === "0" && ph !== 0) ok = false;
        if (placeholders === "1+" && ph < 1) ok = false;
        row.style.display = ok ? "" : "none";
        if (ok) shown += 1;
      });

      if (count) {
        count.textContent = "Showing " + shown + " of " + rows.length + ".";
      }
      var params = new URLSearchParams();
      if (q) params.set("q", q);
      if (computed !== "any") params.set("computed", computed);
      if (topic !== "any") params.set("topic", topic);
      if (placeholders !== "any") params.set("placeholders", placeholders);
      updateQuery(params);
    }

    function readQuery() {
      if (!window.URLSearchParams) return;
      var params = new URLSearchParams(window.location.search);
      ["q", "computed", "topic", "placeholders"].forEach(function (name) {
        var el = document.getElementById(name);
        if (el && params.has(name)) el.value = params.get(name);
      });
    }

    if (form) {
      form.addEventListener("submit", function (event) {
        event.preventDefault();
        applyFilters();
      });
      form.querySelectorAll("input, select").forEach(function (el) {
        el.addEventListener("change", applyFilters);
        if (el.tagName === "INPUT" && el.type === "text") {
          el.addEventListener("input", applyFilters);
        }
      });
      readQuery();
      applyFilters();
    }

    document.querySelectorAll("button.share").forEach(function (button) {
      button.addEventListener("click", function () {
        var status = button.parentElement.querySelector(".share-status");
        button.disabled = true;
        if (status) status.textContent = "Sharing...";
        fetch("/api/gallery/share", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            subject: button.getAttribute("data-subject") || "CSC662",
            seed: Number(button.getAttribute("data-seed")),
            mode: button.getAttribute("data-mode"),
          }),
        }).then(function (response) {
          return response.json().then(function (data) {
            return { ok: response.ok, data: data };
          });
        }).then(function (result) {
          if (!result.ok) throw new Error(result.data.error || "share failed");
          if (status) {
            status.textContent = "";
            var link = document.createElement("a");
            link.href = result.data.gallery_url || "/gallery";
            link.textContent = result.data.existing
              ? "Already shared" : "Shared";
            status.appendChild(link);
          }
          button.hidden = true;
        }).catch(function (error) {
          if (status) status.textContent = error.message;
          button.disabled = false;
        });
      });
    });
  });
})();

/* Job page: share a completed Library paper to the public gallery. */
(function () {
  "use strict";

  document.addEventListener("click", function (event) {
    var link = event.target.closest("a.share-job");
    if (!link) return;
    event.preventDefault();

    var status = link.parentElement.querySelector(".share-job-status");
    var original = link.textContent;
    link.textContent = "Sharing...";
    if (status) status.textContent = "";

    fetch("/api/gallery/share", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        subject: link.getAttribute("data-subject"),
        seed: Number(link.getAttribute("data-seed")),
        mode: link.getAttribute("data-mode"),
      }),
    }).then(function (response) {
      return response.json().then(function (data) {
        return { ok: response.ok, data: data };
      });
    }).then(function (result) {
      if (!result.ok) {
        throw new Error(result.data.error || "share failed");
      }
      link.textContent = result.data.existing
        ? "Already in the public gallery" : "Shared to the public gallery";
      link.href = result.data.gallery_url || "/gallery";
      link.classList.add("share-job-done");
      if (status) status.textContent = "";
    }).catch(function (error) {
      link.textContent = original;
      if (status) status.textContent = error.message;
    });
  });
})();

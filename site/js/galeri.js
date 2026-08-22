(function () {
  "use strict";

  var root = document.getElementById("galeri-root");
  var searchInput = document.getElementById("galeri-search");
  var resultCount = document.getElementById("galeri-result-count");
  var emptyState = document.getElementById("galeri-empty");
  var totalPhotos = 0;

  function normalized(value) {
    return String(value || "")
      .toLocaleLowerCase("id-ID")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }

  function makeElement(tagName, className, text) {
    var element = document.createElement(tagName);
    if (className) element.className = className;
    if (typeof text === "string") element.textContent = text;
    return element;
  }

  function renderPhoto(photo, chapterCaption, chapterTitle) {
    var figure = makeElement("figure", "museum-photo");
    var image = makeElement("img", "museum-photo-image");
    var caption = makeElement("figcaption", "museum-photo-caption", photo.name || chapterTitle);
    var searchableText = [photo.name, chapterCaption, photo.ocr_text].join(" ");

    figure.dataset.search = normalized(searchableText);
    image.loading = "lazy";
    image.decoding = "async";
    image.src = "media/" + photo.file;
    image.alt = photo.name || "Foto " + chapterTitle;

    figure.appendChild(image);
    figure.appendChild(caption);
    return figure;
  }

  function renderChapter(chapter) {
    var section = makeElement("section", "museum-chapter");
    var header = makeElement("header", "museum-chapter-header");
    var title = makeElement("h3", "museum-chapter-title", chapter.judul_manusia);
    var caption = makeElement("p", "museum-chapter-caption", chapter.caption);
    var meta = makeElement("span", "museum-chapter-count", chapter.fotos.length + " foto");
    var gallery = makeElement("div", "gallery museum-grid");

    section.dataset.chapter = chapter.subbab;
    header.appendChild(title);
    header.appendChild(meta);
    section.appendChild(header);
    section.appendChild(caption);

    chapter.fotos.forEach(function (photo) {
      gallery.appendChild(renderPhoto(photo, chapter.caption, chapter.judul_manusia));
      totalPhotos += 1;
    });

    section.appendChild(gallery);
    return section;
  }

  function renderActivity(activityName, chapters) {
    var activity = makeElement("section", "museum-activity");
    var hero = makeElement("header", "museum-activity-hero");
    var heading = makeElement("h2", "museum-activity-title", activityName);
    var photoCount = chapters.reduce(function (sum, chapter) {
      return sum + chapter.fotos.length;
    }, 0);
    var summary = makeElement(
      "p",
      "museum-activity-summary",
      chapters.length + " subbab · " + photoCount + " foto"
    );

    activity.dataset.activity = activityName;
    hero.appendChild(heading);
    hero.appendChild(summary);
    activity.appendChild(hero);

    chapters.forEach(function (chapter) {
      activity.appendChild(renderChapter(chapter));
    });

    return activity;
  }

  function updateResultCount(visiblePhotos, query) {
    if (!resultCount) return;
    resultCount.textContent = query
      ? visiblePhotos + " dari " + totalPhotos + " foto cocok"
      : totalPhotos + " foto · 4 kegiatan · 7 subbab";
  }

  function filterGallery() {
    var query = normalized(searchInput ? searchInput.value : "");
    var terms = query ? query.split(/\s+/) : [];
    var activities = root.querySelectorAll(".museum-activity");
    var visiblePhotos = 0;

    Array.prototype.forEach.call(activities, function (activity) {
      var activityHasMatch = false;
      var chapters = activity.querySelectorAll(".museum-chapter");

      Array.prototype.forEach.call(chapters, function (chapter) {
        var chapterHasMatch = false;
        var photos = chapter.querySelectorAll(".museum-photo");

        Array.prototype.forEach.call(photos, function (photo) {
          var matches = terms.every(function (term) {
            return photo.dataset.search.indexOf(term) !== -1;
          });
          photo.hidden = !matches;
          if (matches) {
            visiblePhotos += 1;
            chapterHasMatch = true;
            activityHasMatch = true;
          }
        });

        chapter.hidden = !chapterHasMatch;
      });

      activity.hidden = !activityHasMatch;
    });

    if (emptyState) emptyState.hidden = visiblePhotos !== 0;
    updateResultCount(visiblePhotos, query);
  }

  function showLoadError(error) {
    root.setAttribute("aria-busy", "false");
    root.replaceChildren();
    var box = makeElement("div", "galeri-load-error");
    var title = makeElement("strong", "", "Galeri belum berhasil dimuat.");
    var detail = makeElement("span", "", error.message || "Data tidak tersedia.");
    var retry = makeElement("button", "icon-btn", "Coba lagi");
    retry.type = "button";
    retry.addEventListener("click", function () { window.location.reload(); });
    box.appendChild(title);
    box.appendChild(detail);
    box.appendChild(retry);
    root.appendChild(box);
    if (resultCount) resultCount.textContent = "Koleksi foto gagal dimuat";
  }

  function loadGallery() {
    root.setAttribute("aria-busy", "true");
    return fetch("data/galeri-v2.json")
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.json();
      })
      .then(function (data) {
        var fragment = document.createDocumentFragment();
        totalPhotos = 0;

        Object.keys(data).forEach(function (activityName) {
          fragment.appendChild(renderActivity(activityName, data[activityName]));
        });

        root.replaceChildren(fragment);
        root.setAttribute("aria-busy", "false");
        updateResultCount(totalPhotos, "");
        if (typeof lightboxInit === "function") lightboxInit();
      })
      .catch(showLoadError);
  }

  if (searchInput) searchInput.addEventListener("input", filterGallery);
  loadGallery();
})();

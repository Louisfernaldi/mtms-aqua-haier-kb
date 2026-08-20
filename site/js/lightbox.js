function lightboxInit() {
  var figs = document.querySelectorAll(".gallery figure");
  if (!figs.length) return;
  var lb = document.getElementById("lightbox");
  var img = lb.querySelector("img");
  var cap = lb.querySelector(".cap");
  var idx = 0;
  var list = [];
  for (var i = 0; i < figs.length; i++) {
    if (figs[i].dataset.lbBound) continue;
    figs[i].dataset.lbBound = "1";
    list.push(figs[i]);
  }
  if (list.length) {
    for (var j = 0; j < list.length; j++) {
      list[j].addEventListener("click", function () {
        var all = document.querySelectorAll(".gallery figure");
        idx = Array.prototype.indexOf.call(all, this);
        var im = this.querySelector("img");
        img.src = im.src;
        img.alt = im.alt || "";
        cap.textContent = im.alt || "";
        lb.classList.add("open");
      });
    }
  }
  if (lb.dataset.bound) return;
  lb.dataset.bound = "1";
  lb.querySelector(".close").addEventListener("click", function () {
    lb.classList.remove("open");
  });
  lb.querySelector(".prev").addEventListener("click", function () {
    var all = document.querySelectorAll(".gallery figure");
    idx = (idx - 1 + all.length) % all.length;
    var im = all[idx].querySelector("img");
    img.src = im.src;
    img.alt = im.alt || "";
    cap.textContent = im.alt || "";
  });
  lb.querySelector(".next").addEventListener("click", function () {
    var all = document.querySelectorAll(".gallery figure");
    idx = (idx + 1) % all.length;
    var im = all[idx].querySelector("img");
    img.src = im.src;
    img.alt = im.alt || "";
    cap.textContent = im.alt || "";
  });
}
function closeLightbox() {
  var lb = document.getElementById("lightbox");
  if (lb) lb.classList.remove("open");
}
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", lightboxInit);
} else {
  lightboxInit();
}

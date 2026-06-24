// Navigation overlay + gallery lightbox. Plain vanilla JS, no dependencies.
(function () {
  "use strict";

  /* ---- Responsive navigation overlay ---- */
  var toggle = document.querySelector(".nav-toggle");
  var overlay = document.getElementById("nav-overlay");
  var closeBtn = overlay && overlay.querySelector(".nav-close");

  function openNav() {
    overlay.hidden = false;
    toggle.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
    var first = overlay.querySelector("a");
    if (first) first.focus();
  }
  function closeNav() {
    overlay.hidden = true;
    toggle.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
    toggle.focus();
  }
  if (toggle && overlay) {
    toggle.addEventListener("click", openNav);
    closeBtn.addEventListener("click", closeNav);
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) closeNav();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !overlay.hidden) closeNav();
    });
  }

  /* ---- Lightbox ---- */
  var lightbox = document.getElementById("lightbox");
  if (!lightbox) return;
  var lbImg = lightbox.querySelector(".lightbox-img");
  var btnClose = lightbox.querySelector(".lightbox-close");
  var btnPrev = lightbox.querySelector(".lightbox-prev");
  var btnNext = lightbox.querySelector(".lightbox-next");
  var items = Array.prototype.slice.call(document.querySelectorAll(".gallery-item"));
  var current = -1;

  function show(i) {
    if (i < 0) i = items.length - 1;
    if (i >= items.length) i = 0;
    current = i;
    var link = items[i];
    var img = link.querySelector("img");
    lbImg.src = link.getAttribute("href");
    lbImg.alt = img ? img.alt : "";
  }
  function openLb(i) {
    show(i);
    lightbox.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }
  function closeLb() {
    lightbox.setAttribute("aria-hidden", "true");
    lbImg.src = "";
    document.body.style.overflow = "";
  }

  items.forEach(function (link, i) {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      openLb(i);
    });
  });
  btnClose.addEventListener("click", closeLb);
  btnPrev.addEventListener("click", function () { show(current - 1); });
  btnNext.addEventListener("click", function () { show(current + 1); });
  lightbox.addEventListener("click", function (e) {
    if (e.target === lightbox) closeLb();
  });
  document.addEventListener("keydown", function (e) {
    if (lightbox.getAttribute("aria-hidden") === "true") return;
    if (e.key === "Escape") closeLb();
    else if (e.key === "ArrowLeft") show(current - 1);
    else if (e.key === "ArrowRight") show(current + 1);
  });
})();

/* Baseplate Wiki — client-side search + mobile nav.
   No dependencies, no backend. The index is a static JSON file, so this works
   on GitHub Pages or any dumb static host. */

(function () {
  "use strict";

  var base = document.body.getAttribute("data-base") || "";

  /* ------------------------------------------------------------- theme */

  var root = document.documentElement;
  var themeButton = document.querySelector(".theme");

  function currentTheme() {
    var explicit = root.getAttribute("data-theme");
    if (explicit) return explicit;
    return window.matchMedia("(prefers-color-scheme: light)").matches
      ? "light" : "dark";
  }

  if (themeButton) {
    themeButton.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("bp-theme", next); } catch (e) {}
    });
  }

  /* If the reader has never chosen, keep following the OS while they change it */
  window.matchMedia("(prefers-color-scheme: light)").addEventListener(
    "change",
    function () {
      var saved = null;
      try { saved = localStorage.getItem("bp-theme"); } catch (e) {}
      if (!saved) root.removeAttribute("data-theme");
    }
  );

  /* ---------------------------------------------------------- mobile nav */

  var menu = document.querySelector(".menu");
  var side = document.getElementById("side");
  if (menu && side) {
    menu.addEventListener("click", function () {
      var open = side.classList.toggle("open");
      menu.classList.toggle("is-open", open);
      menu.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  /* -------------------------------------------------------- copy buttons */

  /* The button is rendered server-side inside the code bar, so there is no
     layout shift and it still exists with JS disabled (it just does nothing
     until this runs). */
  document.querySelectorAll(".code .copy").forEach(function (btn) {
    var block = btn.closest(".code");
    var pre = block && block.querySelector("pre");
    if (!pre) return;

    var label = btn.querySelector(".copy-text");

    function flash(text) {
      btn.classList.add("done");
      if (label) label.textContent = text;
      setTimeout(function () {
        btn.classList.remove("done");
        if (label) label.textContent = "Copy";
      }, 1600);
    }

    function fallback(text) {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); flash("Copied"); }
      catch (e) { if (label) label.textContent = "Ctrl+C"; }
      document.body.removeChild(ta);
    }

    btn.addEventListener("click", function () {
      var text = pre.innerText;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(
          function () { flash("Copied"); },
          function () { fallback(text); }
        );
      } else {
        fallback(text);
      }
    });
  });

  /* ------------------------------------------------------- term previews */

  /* Hover card for auto-linked glossary terms. Hover only -- on touch there is
     no hover state, and tapping should just follow the link, so this quietly
     does nothing there. Keyboard focus opens it too, so it is not mouse-only. */
  (function () {
    var links = document.querySelectorAll(".term-link[data-summary]");
    if (!links.length) return;
    if (!window.matchMedia("(hover: hover)").matches) return;

    var card = document.createElement("div");
    card.className = "term-pop";
    card.setAttribute("role", "tooltip");
    card.hidden = true;
    document.body.appendChild(card);

    var showTimer = null, hideTimer = null, current = null;

    function place(link) {
      var r = link.getBoundingClientRect();
      var margin = 10;

      card.hidden = false;
      card.style.left = "0px";
      card.style.top = "0px";
      var cw = card.offsetWidth, ch = card.offsetHeight;

      /* prefer above; flip below when there is not room */
      var top = r.top - ch - 8;
      var below = false;
      if (top < margin) {
        top = r.bottom + 8;
        below = true;
      }

      /* centre on the link, then clamp inside the viewport */
      var left = r.left + r.width / 2 - cw / 2;
      left = Math.max(margin, Math.min(left, window.innerWidth - cw - margin));

      card.style.left = Math.round(left + window.scrollX) + "px";
      card.style.top = Math.round(top + window.scrollY) + "px";
      card.classList.toggle("below", below);
    }

    function show(link) {
      current = link;
      card.innerHTML =
        '<strong></strong><span></span><em>Read the full entry &rarr;</em>';
      card.querySelector("strong").textContent = link.dataset.term || "";
      card.querySelector("span").textContent = link.dataset.summary || "";
      place(link);
      /* Force a reflow rather than waiting on requestAnimationFrame: rAF is
         throttled in background/hidden tabs, which left the card populated and
         positioned but permanently invisible. */
      void card.offsetWidth;
      card.classList.add("on");
    }

    function hide() {
      current = null;
      card.classList.remove("on");
      hideTimer = setTimeout(function () { card.hidden = true; }, 140);
    }

    links.forEach(function (link) {
      function open() {
        clearTimeout(hideTimer);
        clearTimeout(showTimer);
        showTimer = setTimeout(function () { show(link); }, 180);
      }
      function close() {
        clearTimeout(showTimer);
        hideTimer = setTimeout(hide, 120);
      }

      link.addEventListener("mouseenter", open);
      link.addEventListener("mouseleave", close);
      link.addEventListener("focus", open);
      link.addEventListener("blur", close);
    });

    /* keep it open while the pointer is on the card itself */
    card.addEventListener("mouseenter", function () { clearTimeout(hideTimer); });
    card.addEventListener("mouseleave", hide);

    window.addEventListener("scroll", function () {
      if (current) place(current);
    }, { passive: true });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && current) hide();
    });
  })();

  /* ------------------------------------------------------------- search */

  var input = document.getElementById("q");
  var box = document.getElementById("results");
  if (!input || !box) return;

  var index = null;
  var loading = false;
  var cursor = -1;

  function load() {
    if (index || loading) return Promise.resolve();
    loading = true;
    return fetch(base + "search-index.json")
      .then(function (r) { return r.json(); })
      .then(function (data) { index = data; loading = false; })
      .catch(function () {
        loading = false;
        box.innerHTML = '<p class="none">Search index failed to load.</p>';
        box.hidden = false;
      });
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  /* Mark the matched run inside a title. */
  function mark(text, terms) {
    var out = esc(text);
    terms.forEach(function (t) {
      if (!t) return;
      var re = new RegExp("(" + t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
      out = out.replace(re, "<mark>$1</mark>");
    });
    return out;
  }

  /* Score a document. Title hits beat heading hits beat body hits, and every
     term must appear somewhere or the doc is out — that keeps two-word queries
     from returning half the site. */
  function score(doc, terms) {
    var title = doc.t.toLowerCase();
    var head = (doc.h || []).join(" ").toLowerCase();
    var body = ((doc.d || "") + " " + (doc.b || "")).toLowerCase();
    var cat = (doc.c || "").toLowerCase();
    var total = 0;

    for (var i = 0; i < terms.length; i++) {
      var t = terms[i];
      var s = 0;
      if (title.indexOf(t) === 0) s += 60;
      else if (title.indexOf(t) !== -1) s += 40;
      if (head.indexOf(t) !== -1) s += 12;
      if (cat.indexOf(t) !== -1) s += 8;
      if (body.indexOf(t) !== -1) s += 4;
      if (s === 0) return 0;      // missing term -> not a match
      total += s;
    }
    return total;
  }

  function render(query) {
    var terms = query.toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length || !index) {
      box.hidden = true;
      box.innerHTML = "";
      return;
    }

    var hits = [];
    for (var i = 0; i < index.length; i++) {
      var s = score(index[i], terms);
      if (s > 0) hits.push({ d: index[i], s: s });
    }
    hits.sort(function (a, b) { return b.s - a.s; });
    hits = hits.slice(0, 10);

    if (!hits.length) {
      box.innerHTML = '<p class="none">No matches for &ldquo;' + esc(query) +
        '&rdquo;.</p>';
      box.hidden = false;
      return;
    }

    box.innerHTML = hits.map(function (h) {
      var meta = [h.d.k, h.d.c].filter(Boolean).join(" · ");
      return '<a href="' + base + h.d.u + '"><strong>' +
        mark(h.d.t, terms) + "</strong><em>" + esc(meta) + "</em></a>";
    }).join("");
    box.hidden = false;
    cursor = -1;
  }

  var timer = null;
  input.addEventListener("input", function () {
    var q = input.value.trim();
    if (!q) { box.hidden = true; return; }
    clearTimeout(timer);
    timer = setTimeout(function () {
      load().then(function () { render(q); });
    }, 90);
  });

  input.addEventListener("focus", load);

  /* keyboard: arrows move, Enter opens, Escape closes */
  input.addEventListener("keydown", function (e) {
    var items = box.querySelectorAll("a");

    if (e.key === "Escape") {
      box.hidden = true;
      input.blur();
      return;
    }
    if (!items.length) return;

    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      cursor += e.key === "ArrowDown" ? 1 : -1;
      if (cursor < 0) cursor = items.length - 1;
      if (cursor >= items.length) cursor = 0;
      for (var i = 0; i < items.length; i++) {
        items[i].classList.toggle("on", i === cursor);
      }
      items[cursor].scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter" && cursor >= 0) {
      e.preventDefault();
      window.location.href = items[cursor].getAttribute("href");
    }
  });

  document.addEventListener("click", function (e) {
    if (!e.target.closest(".search")) box.hidden = true;
  });

  /* "/" focuses search, the convention on every docs site */
  document.addEventListener("keydown", function (e) {
    if (e.key === "/" && document.activeElement !== input &&
        !/^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName)) {
      e.preventDefault();
      input.focus();
    }
  });
})();

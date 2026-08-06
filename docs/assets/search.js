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

  /* ------------------------------------------------- saved pages (local) */

  /* localStorage, not cookies: this never needs to reach a server, and cookies
     would be sent on every request for no reason. */
  var SAVED_KEY = "bp-saved";

  function readSaved() {
    try {
      var raw = localStorage.getItem(SAVED_KEY);
      var v = raw ? JSON.parse(raw) : [];
      return Array.isArray(v) ? v : [];
    } catch (e) { return []; }
  }

  function writeSaved(list) {
    try { localStorage.setItem(SAVED_KEY, JSON.stringify(list)); } catch (e) {}
    paintSavedCount();
  }

  function paintSavedCount() {
    var n = readSaved().length;
    document.querySelectorAll(".saved-count").forEach(function (el) {
      el.textContent = n;
      el.hidden = n === 0;
    });
  }

  paintSavedCount();

  /* ------------------------------------------------------------- feedback */

  document.querySelectorAll(".feedback").forEach(function (box) {
    var pageId = box.dataset.page;
    var done = box.querySelector(".fb-done");
    var ask = box.querySelector(".fb-ask");
    var endpoint = document.body.dataset.feedback || "";
    var voteKey = "bp-vote:" + pageId;

    /* ---- save button */
    var saveBtn = box.querySelector(".fb-save");
    var saveText = box.querySelector(".fb-save-text");

    function paintSave() {
      var on = readSaved().some(function (i) { return i.u === pageId; });
      saveBtn.classList.toggle("on", on);
      saveBtn.setAttribute("aria-pressed", on ? "true" : "false");
      if (saveText) saveText.textContent = on ? "Saved" : "Save";
    }

    saveBtn.addEventListener("click", function () {
      var list = readSaved();
      var i = list.findIndex(function (x) { return x.u === pageId; });
      if (i >= 0) {
        list.splice(i, 1);
      } else {
        var h1 = document.querySelector(".doc h1");
        var lede = document.querySelector(".doc .lede");
        list.unshift({
          u: pageId,
          t: h1 ? h1.textContent.trim() : document.title,
          d: lede ? lede.textContent.trim() : "",
          at: Date.now()
        });
        list = list.slice(0, 200);
      }
      writeSaved(list);
      paintSave();
    });

    paintSave();

    /* ---- helpful / not helpful */
    function record(vote, reason) {
      if (!endpoint) return;              // static site: nowhere to send it
      try {
        var body = new FormData();
        body.append("page", pageId);
        body.append("vote", vote);
        if (reason) body.append("reason", reason);
        fetch(endpoint, { method: "POST", body: body, mode: "no-cors" });
      } catch (e) {}
    }

    function thanks(msg) {
      ask.hidden = true;
      done.hidden = false;
      done.innerHTML = "";
      var p = document.createElement("p");
      p.textContent = msg;
      done.appendChild(p);
      return done;
    }

    function showReport() {
      var wrap = thanks("Sorry about that. What went wrong?");

      var reasons = [
        ["code", "The code didn't work"],
        ["outdated", "It's out of date"],
        ["unclear", "I couldn't follow it"],
        ["missing", "It didn't cover my case"]
      ];

      var row = document.createElement("div");
      row.className = "fb-reasons";
      reasons.forEach(function (r) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "fb-reason";
        b.textContent = r[1];
        b.addEventListener("click", function () {
          record("down", r[0]);
          var out = thanks("Thanks \u2014 that helps.");
          var links = document.createElement("p");
          links.className = "fb-links";
          links.innerHTML =
            '<a href="' + box.dataset.issue + '" target="_blank" rel="noopener">' +
            "Report it on GitHub</a> or <a href=\"" + box.dataset.mail +
            '">send an email</a>. Including the exact error text makes it fixable.';
          out.appendChild(links);
        });
        row.appendChild(b);
      });
      wrap.appendChild(row);
    }

    box.querySelectorAll(".fb-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var vote = btn.dataset.vote;
        try { localStorage.setItem(voteKey, vote); } catch (e) {}

        if (vote === "up") {
          record("up");
          thanks("Thanks \u2014 glad it helped.");
        } else {
          showReport();
        }
      });
    });

    /* already voted on this page before: don't ask again */
    try {
      var prev = localStorage.getItem(voteKey);
      if (prev === "up") thanks("You marked this helpful.");
      else if (prev === "down") thanks("You reported a problem with this page.");
    } catch (e) {}
  });

  /* --------------------------------------------------------- saved page */

  (function () {
    var host = document.getElementById("saved-list");
    if (!host) return;

    var list = readSaved();

    function render() {
      list = readSaved();
      if (!list.length) {
        host.innerHTML =
          '<p class="empty-note">Nothing saved yet. Open any guide and press ' +
          "<strong>Save</strong> at the bottom to keep it here.</p>";
        return;
      }

      var ul = document.createElement("ul");
      ul.className = "rows";

      list.forEach(function (item) {
        var li = document.createElement("li");
        li.className = "row";

        var a = document.createElement("a");
        a.href = base + item.u;

        var h3 = document.createElement("h3");
        h3.textContent = item.t;
        a.appendChild(h3);

        if (item.d) {
          var p = document.createElement("p");
          p.textContent = item.d;
          a.appendChild(p);
        }
        li.appendChild(a);

        var rm = document.createElement("button");
        rm.type = "button";
        rm.className = "saved-remove";
        rm.textContent = "Remove";
        rm.addEventListener("click", function () {
          writeSaved(readSaved().filter(function (x) { return x.u !== item.u; }));
          render();
        });
        li.appendChild(rm);

        ul.appendChild(li);
      });

      host.innerHTML = "";
      host.appendChild(ul);
    }

    render();
  })();

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

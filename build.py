#!/usr/bin/env python3
"""Baseplate Wiki static site builder.

Reads Markdown from content/ and writes HTML into site/.
Pure stdlib -- no pip install, no build tools, no client-side framework.

Usage:
    python3 build.py
"""

import html
import json
import re
import shutil
from datetime import date
from pathlib import Path

import hashlib

from luau import highlight_block
from terms import link_terms, load_terms

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
SITE = ROOT / "docs"   # "docs" because GitHub Pages only publishes / or /docs

SITE_NAME = "Baseplate Wiki"
SITE_SHORT = "Baseplate"
SITE_TAGLINE = ("An open reference for Roblox game development. Written and "
                "tested by hand, corrections welcome.")
SITE_URL = "https://richyrach.github.io/baseplate-wiki"

# Ad slots stay as HTML comments until AdSense approves the site. Empty ad
# containers on an unapproved site is literally the "Google-served ads on
# screens without publisher-content" rejection, so this must remain False
# until the approval email arrives.
ADS_ENABLED = False

# Two kinds of page, because they are read completely differently.
# learn  = teaching. Read in order, explains why. "What a RemoteEvent is."
# recipe = task. Landed on from a search, copied, left. "Change the weather."
SECTIONS = {
    "learn": {
        "title": "Learn",
        "blurb": "Explanations you read once, in order, to understand how "
                 "something works.",
    },
    "recipe": {
        "title": "Recipes",
        "blurb": "Self-contained answers to one specific task. Land, copy, "
                 "get back to building.",
    },
}

CATEGORIES = [
    "Scripting", "Building", "Vehicles", "UI",
    "Data", "Multiplayer", "Animation", "Monetization", "Performance",
]

CATEGORY_BLURBS = {
    "Scripting": "The client-server boundary, RemoteEvents, and the errors that "
                 "come from getting them backwards.",
    "Building": "Parts, welds, models and terrain. Making things that hold "
                "together once the game runs.",
    "Vehicles": "A-Chassis, spawning, handling, and why your car keeps flipping.",
    "UI": "ScreenGuis that survive phone screens, and buttons the server trusts.",
    "Data": "DataStores, saving player progress, and not losing it on shutdown.",
    "Multiplayer": "Teams, rounds, matchmaking, and what only breaks with real "
                   "players in the server.",
    "Animation": "Rigs, tweens, and animations that play for everyone instead of "
                 "just you.",
    "Monetization": "Game passes, developer products, receipts and Premium. The "
                    "code that touches real money, and the checks that keep it "
                    "honest.",
    "Performance": "Why it ran fine with two players, and what to measure first.",
}

# Category marks, hand-written paths. A stock icon set is the fastest way to
# look like every other template.
CATEGORY_ICONS = {
    "Scripting": '<path d="M9.2 6.6 4.8 12l4.3 5.5"/><path d="M14.9 6.5 19.3 12 15 17.5"/>'
                 '<path d="M13.2 5.9 11 18.2"/>',
    "Building": '<path d="M3.6 14.4h6.1v5.1H3.7z"/><path d="M13.9 14.3h6.2v5.2h-6.1z"/>'
                '<path d="M8.7 8.9h6.2v5.2H8.8z"/>',
    "Vehicles": '<path d="M3.2 14.7c.3-1.4.7-3.1 1.9-3.6 1.6-.7 3.6-1 6.7-1 '
                '2.5 0 4.2 1.1 5.7 2.3l2.4.7c1 .3 1.2.9 1.2 1.5v1.2h-2.2"/>'
                '<path d="M9.6 15.8H14"/><circle cx="7.4" cy="16.1" r="2"/>'
                '<circle cx="16.4" cy="16" r="2"/>',
    "UI": '<path d="M4.1 5.6h15.8v12.9H4.2z"/><path d="M4.2 9.3h15.6"/>'
          '<path d="M6.9 12.4h5.2v3.1H6.9z"/>',
    "Data": '<path d="M5.1 7.3c0-1.3 3.1-2.3 6.9-2.3 3.9 0 7 1 7 2.3 0 1.2-3.1 '
            '2.2-7 2.2-3.8 0-6.9-1-6.9-2.2z"/>'
            '<path d="M5.1 7.4v9.4c0 1.3 3.1 2.3 6.9 2.3 3.9 0 7-1 7-2.3V7.3"/>'
            '<path d="M5.2 12.1c0 1.2 3 2.2 6.8 2.2 3.9 0 7-1 7-2.2"/>',
    "Multiplayer": '<circle cx="9.1" cy="9.2" r="2.7"/>'
                   '<path d="M4.2 18.9c0-2.9 2.1-4.6 4.8-4.6 2.8 0 4.9 1.7 4.9 4.6"/>'
                   '<circle cx="16.6" cy="10.6" r="2.1"/>'
                   '<path d="M14.6 18.9c.2-2.3 1.3-3.6 3-3.6 1.8 0 2.9 1.3 3.1 3.6"/>',
    "Animation": '<path d="M3.6 19h16.6"/>'
                 '<path d="M7.4 8.1l2.3 2.3-2.3 2.4-2.3-2.4z"/>'
                 '<path d="M11.4 13.1c2.1-1.1 3.6-2.9 4.7-5.4"/>'
                 '<circle cx="17.6" cy="6.1" r="1.5"/>',
    "Monetization": '<circle cx="12" cy="12" r="7.6"/>'
                    '<path d="M12 7.6v8.8"/>'
                    '<path d="M14.5 9.8c-.5-.8-1.4-1.3-2.5-1.3-1.4 0-2.4.7-2.4 1.8 '
                    '0 1 .8 1.5 2.4 1.8 1.7.3 2.6.8 2.6 1.9 0 1.2-1.1 1.9-2.6 1.9'
                    '-1.2 0-2.2-.5-2.7-1.4"/>',
    "Performance": '<path d="M4.4 17.1a7.6 7.6 0 0 1 15.2 0"/>'
                   '<path d="M12 17.1 15.7 11.6"/><path d="M6.4 11.3l.9.9"/>'
                   '<path d="M12 8.6v1.3"/><path d="M17.6 11.3l-.9.9"/>',
}


def asset_version(name):
    """Short content hash for cache-busting.

    GitHub Pages serves CSS and JS with caching headers, so without this a
    reader who has visited before keeps the OLD stylesheet after an update --
    which looks exactly like the site being broken again.
    """
    src = ROOT / "templates" / name
    if not src.exists():
        return "0"
    return hashlib.sha1(src.read_bytes()).hexdigest()[:8]


ASSET_V = {}


def icon(name, cls="ico"):
    paths = CATEGORY_ICONS.get(name, "")
    if not paths:
        return ""
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{paths}</svg>')


def ad(slot):
    """An ad position. Until approval this emits only a comment, so the page
    never ships an empty ad container."""
    if not ADS_ENABLED:
        return f"<!-- ad slot '{slot}': paste AdSense code here AFTER approval -->"
    return (f'<div class="ad" data-slot="{slot}">'
            f'<span class="ad-label">Advertisement</span></div>')


def tabs(depth=0, active=""):
    """Top switcher: Learn / Recipes / Reference."""
    up = "../" * depth
    items = [("Learn", "learn.html"), ("Recipes", "recipes.html"),
             ("Reference", "terms/index.html")]
    out = []
    for label, url in items:
        on = ' class="on"' if url == active else ""
        out.append(f'<a{on} href="{up}{url}">{label}</a>')
    return f'<nav class="tabs">{"".join(out)}</nav>'


# ---------------------------------------------------------------- front matter

def parse_front_matter(text):
    meta = {}
    if not text.startswith("---"):
        return meta, text
    end = text.find("\n---", 3)
    if end == -1:
        return meta, text
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            value = value.strip()
            # drafts often arrive YAML-quoted; strip a matched pair
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1].strip()
            meta[key.strip()] = value
    return meta, text[end + 4:].lstrip("\n")


# ------------------------------------------------------------------- markdown

def inline(text):
    spans = []

    def stash(m):
        spans.append(m.group(1))
        return f"\x00{len(spans) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
                  r'<img src="\2" alt="\1" loading="lazy">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\w)", r"<em>\1</em>", text)

    def restore(m):
        return f'<code>{html.escape(spans[int(m.group(1))], quote=False)}</code>'

    return re.sub(r"\x00(\d+)\x00", restore, text)


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def strip_tags(text):
    return re.sub(r"<[^>]+>", "", text)


def render(md):
    """Markdown subset -> (html, toc)."""
    out, toc = [], []
    lines = md.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            lang = line[3:].strip().lower()
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            label = {"lua": "Luau", "luau": "Luau", "bash": "Shell",
                     "text": "Tree", "json": "JSON"}.get(lang, lang.upper())
            body = highlight_block("\n".join(code), lang)
            head = f'<span class="code-lang">{label}</span>' if lang else ""
            out.append(f'<div class="code">{head}<pre><code>{body}</code></pre></div>')
            continue

        m = re.match(r"^> \[!(\w+)\]\s*(.*)", line)
        if m:
            kind, first = m.group(1).lower(), m.group(2)
            body = [first] if first else []
            i += 1
            while i < len(lines) and lines[i].startswith("> "):
                body.append(lines[i][2:])
                i += 1
            out.append(f'<aside class="note note-{kind}">'
                       f'<p class="note-label">{kind}</p>'
                       f"<p>{inline(' '.join(body))}</p></aside>")
            continue

        if (line.lstrip().startswith("|") and i + 1 < len(lines)
                and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1])):
            def cells(row):
                return [c.strip() for c in row.strip().strip("|").split("|")]
            head = cells(line)
            i += 2
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            thead = "".join(f"<th>{inline(c)}</th>" for c in head)
            tbody = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r)
                            + "</tr>" for r in rows)
            out.append(f'<div class="table-scroll"><table><thead><tr>{thead}</tr>'
                       f"</thead><tbody>{tbody}</tbody></table></div>")
            continue

        m = re.match(r"^(#{2,4})\s+(.*)", line)
        if m:
            level, text = len(m.group(1)), m.group(2)
            anchor = slugify(text)
            if level == 2:
                toc.append((anchor, text))
            out.append(f'<h{level} id="{anchor}">{inline(text)}'
                       f'<a class="anchor" href="#{anchor}" aria-label="Link to '
                       f'this section">#</a></h{level}>')
            i += 1
            continue

        if re.match(r"^\s*[-*]\s+", line) or re.match(r"^\s*\d+\.\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.\s+", line))
            pattern = r"^\s*\d+\.\s+" if ordered else r"^\s*[-*]\s+"
            items = []
            while i < len(lines) and re.match(pattern, lines[i]):
                items.append(re.sub(pattern, "", lines[i]))
                i += 1
            tag = "ol" if ordered else "ul"
            body = "".join(f"<li>{inline(x)}</li>" for x in items)
            out.append(f"<{tag}>{body}</{tag}>")
            continue

        if not line.strip():
            i += 1
            continue

        para = []
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{2,4}\s|```|>\s|\s*\||\s*[-*]\s|\s*\d+\.\s)", lines[i]):
            para.append(lines[i])
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")

    return "\n".join(out), toc


# -------------------------------------------------------------------- chrome

def sidebar(depth, active_url="", active_cat="", guides=None):
    """Search + category browse. Learn/Recipes/Reference live in the top tabs,
    so listing them here as well was pure duplication."""
    up = "../" * depth
    guides = guides or []

    cats = []
    for c in CATEGORIES:
        n = sum(1 for g in guides if g["category"] == c)
        on = ' aria-current="page"' if c == active_cat else ""
        dim = ' class="empty"' if not n else ""
        cats.append(f'<li{dim}><a{on} href="{up}c/{slugify(c)}.html">'
                    f'{icon(c)}<span>{c}</span><em>{n}</em></a></li>')

    return f"""<aside class="side" id="side">
  <form class="search" role="search" onsubmit="return false">
    <label class="sr" for="q">Search the wiki</label>
    <input id="q" type="search" placeholder="Search&hellip;  /"
           autocomplete="off" spellcheck="false">
    <div id="results" class="results" hidden></div>
  </form>
  <nav class="side-nav">
    <p class="side-label">Categories</p>
    <ul class="side-list side-cats">{''.join(cats)}</ul>
    <div class="side-more">
      <p class="side-label">More</p>
      <ul class="side-list">
        <li><a href="{up}about.html"><span>About</span></a></li>
        <li><a href="{up}contribute.html"><span>Contribute</span></a></li>
        <li><a href="{up}contact.html"><span>Contact</span></a></li>
      </ul>
    </div>
  </nav>
</aside>"""


def page(title, description, body, depth=0, active_url="", active_cat="",
         guides=None, extra_class="", chrome=True, active_tab=""):
    """chrome=False drops the sidebar -- used for articles, which read better
    full width and leave room for an ad rail."""
    up = "../" * depth
    # The sidebar is always rendered. On article pages it is hidden at desktop
    # width (so the article runs full width) but still reachable from the mobile
    # drawer -- otherwise a reader arriving from a search engine has no way to
    # search the site at all.
    shell_class = "shell" if chrome else "shell shell-wide"
    shell = (f'<div class="{shell_class}">'
             f'{sidebar(depth, active_url, active_cat, guides)}')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="stylesheet" href="{up}assets/style.css?v={ASSET_V.get('style.css', '0')}">
<script>
/* Runs before first paint: without this the page renders in the OS theme and
   then snaps to the saved one, which is a visible flash on every navigation. */
(function () {{
  try {{
    var saved = localStorage.getItem("bp-theme");
    if (saved === "light" || saved === "dark") {{
      document.documentElement.setAttribute("data-theme", saved);
    }}
  }} catch (e) {{}}
}})();
</script>
</head>
<body data-base="{up}" class="{extra_class}">
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <button class="menu" aria-expanded="false" aria-controls="side">Menu</button>
  <a class="brand" href="{up}index.html">{SITE_SHORT}<span>Wiki</span></a>
  {tabs(depth, active_tab)}
  <nav class="top-links">
    <a href="{up}about.html">About</a>
    <a href="{up}contribute.html">Contribute</a>
  </nav>
  <button class="theme" type="button" aria-label="Switch between light and dark"
          title="Switch theme">
    <svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         stroke-width="1.8" stroke-linecap="round" aria-hidden="true">
      <circle cx="12" cy="12" r="4.2"/>
      <path d="M12 2.4v2.4M12 19.2v2.4M4.2 4.2l1.7 1.7M18.1 18.1l1.7 1.7M2.4 12h2.4M19.2 12h2.4M4.2 19.8l1.7-1.7M18.1 5.9l1.7-1.7"/>
    </svg>
    <svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"
         aria-hidden="true">
      <path d="M20.1 14.3A8.4 8.4 0 0 1 9.6 3.9a8.4 8.4 0 1 0 10.5 10.4z"/>
    </svg>
  </button>
</header>
{shell}
<main id="main">
{body}
</main>
</div>
<footer class="foot">
  <p>{SITE_NAME} &mdash; written and tested by hand in Roblox Studio.
     Open to corrections: <a href="{up}contribute.html">contribute</a>.</p>
  <p class="fine">&copy; {date.today().year} {SITE_NAME}. Not affiliated with or
     endorsed by Roblox Corporation.
     <a href="{up}privacy.html">Privacy</a></p>
</footer>
<script src="{up}assets/search.js?v={ASSET_V.get('search.js', '0')}" defer></script>
</body>
</html>
"""


# ---------------------------------------------------------------------- build

def read_guides(glossary=None):
    guides = []
    for path in sorted((CONTENT / "guides").glob("*.md")):
        meta, md = parse_front_matter(path.read_text(encoding="utf-8"))

        needs_experience = "OWN_EXPERIENCE" in md
        md = re.sub(r"^[ \t]*<!--.*?-->[ \t]*\n?", "", md, flags=re.MULTILINE)

        category = meta.get("category", "").strip()
        if category not in CATEGORIES:
            if category:
                print(f"  warning: {path.name} category {category!r} unknown "
                      f"-- filed under Scripting")
            category = "Scripting"

        kind = meta.get("kind", "learn").strip().lower()
        if kind not in SECTIONS:
            if kind:
                print(f"  warning: {path.name} kind {kind!r} unknown -- "
                      f"treated as learn")
            kind = "learn"

        body, toc = render(md)
        if glossary:
            body, _ = link_terms(body, glossary, depth=1)
        guides.append({
            "slug": path.stem,
            "title": meta.get("title", path.stem),
            "description": meta.get("description", ""),
            "date": meta.get("date", ""),
            "updated": meta.get("updated", "").strip() or meta.get("date", ""),
            "level": meta.get("level", ""),
            "minutes": meta.get("minutes", ""),
            "category": category,
            "kind": kind,
            "needs_experience": needs_experience,
            "body": body,
            "toc": toc,
        })
    guides.sort(key=lambda g: g["date"], reverse=True)
    return guides


def row(g, depth=0):
    """One guide in a list. Dense row, not a card."""
    up = "../" * depth
    bits = [SECTIONS[g["kind"]]["title"], g["category"], g["level"]]
    if g["minutes"]:
        bits.append(f"{g['minutes']} min")
    meta = "".join(f"<span>{b}</span>" for b in bits if b)
    return f"""<li class="row row-{g['kind']}">
  <a href="{up}guides/{g['slug']}.html">
    <h3>{html.escape(g['title'])}</h3>
    <p>{html.escape(g['description'])}</p>
    <p class="row-meta">{meta}</p>
  </a>
</li>"""


def build_guide(g, guides):
    toc = ""
    if len(g["toc"]) > 2:
        items = "".join(f'<li><a href="#{a}">{html.escape(tt)}</a></li>'
                        for a, tt in g["toc"])
        toc = (f'<aside class="rail"><p class="rail-label">On this page</p>'
               f"<ul>{items}</ul></aside>")

    bits = [b for b in [g["category"], g["level"],
                        f"{g['minutes']} min read" if g["minutes"] else ""] if b]
    meta = "".join(f"<span>{b}</span>" for b in bits)
    cat_slug = slugify(g["category"])
    sect = SECTIONS[g["kind"]]
    sect_url = f"{g['kind']}{'s' if g['kind'] == 'recipe' else ''}.html"

    edited = ""
    if g["updated"]:
        same = g["updated"] == g["date"]
        label = "Published" if same else "Last edited"
        edited = (f'<p class="edited"><time datetime="{g["updated"]}">'
                  f'{label} {g["updated"]}</time>'
                  f' &middot; <a href="../contribute.html">suggest an edit</a></p>')

    body = f"""<article class="doc">
  <p class="crumbs">
    <a href="../{sect_url}">{sect['title']}</a>
    <span aria-hidden="true">/</span>
    <a href="../c/{cat_slug}.html">{html.escape(g['category'])}</a>
  </p>
  <h1>{html.escape(g['title'])}</h1>
  <p class="lede">{html.escape(g['description'])}</p>
  <p class="doc-meta">{meta}</p>
  {ad('article-top')}
  {toc}
  <div class="prose">
{g['body']}
  </div>
  {ad('article-end')}
  <footer class="doc-foot">
    {edited}
    <p>Found a mistake in this guide? <a href="../contribute.html">Send a
       correction</a> &mdash; every page here is open to edits.</p>
  </footer>
</article>"""

    out = SITE / "guides" / f"{g['slug']}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page(f"{g['title']} — {SITE_NAME}", g["description"], body,
                        depth=1, guides=guides, extra_class="has-rail",
                        chrome=False, active_tab=sect_url),
                   encoding="utf-8")


def build_terms(glossary, guides):
    """One page per term, plus an A-Z reference index."""
    out_dir = SITE / "terms"
    out_dir.mkdir(parents=True, exist_ok=True)

    for term in glossary:
        body_html, _ = link_terms(term["body"], glossary,
                                  current_slug=term["slug"], depth=1)
        cat = term["category"]
        crumb = (f'<a href="../c/{slugify(cat)}.html">{html.escape(cat)}</a>'
                 if cat in CATEGORIES else "")
        related = [g for g in guides if g["category"] == cat][:4]
        rel = ""
        if related:
            links = "".join(
                f'<li><a href="../guides/{r["slug"]}.html">'
                f'{html.escape(r["title"])}</a></li>' for r in related)
            rel = (f'<section class="related"><h2>Guides that use this</h2>'
                   f"<ul>{links}</ul></section>")

        body = f"""<article class="doc doc-term">
  <p class="crumbs"><a href="index.html">Reference</a>
    {'<span aria-hidden="true">/</span>' + crumb if crumb else ''}</p>
  <h1><code class="term-title">{html.escape(term['term'])}</code></h1>
  <p class="lede">{html.escape(term['summary'])}</p>
  {ad('term-top')}
  <div class="prose">
{body_html}
  </div>
  {rel}
  <footer class="doc-foot">
    <p>Something wrong or missing here?
       <a href="../contribute.html">Send a correction</a>.</p>
  </footer>
</article>"""
        (out_dir / f"{term['slug']}.html").write_text(
            page(f"{term['term']} — {SITE_NAME} reference",
                 term["summary"], body, depth=1, guides=guides,
                 chrome=False, active_tab="terms/index.html"),
            encoding="utf-8")

    # index, grouped by first letter
    groups = {}
    for term in sorted(glossary, key=lambda x: x["term"].lower()):
        groups.setdefault(term["term"][0].upper(), []).append(term)

    blocks = []
    for letter in sorted(groups):
        rows = "".join(
            f'<li><a href="{t2["slug"]}.html"><code>{html.escape(t2["term"])}</code>'
            f'<span>{html.escape(t2["summary"])}</span></a></li>'
            for t2 in groups[letter])
        blocks.append(f'<h2 class="az">{letter}</h2><ul class="term-list">{rows}</ul>')

    listing = "".join(blocks) or (
        '<p class="empty-note">No reference entries yet.</p>')

    body = f"""<div class="page-head">
  <h1>Reference</h1>
  <p class="lede">Plain-language explanations of the objects, events and
     properties that come up constantly. {len(glossary)} entries.</p>
</div>
{listing}
{ad('list-foot')}"""
    (out_dir / "index.html").write_text(
        page(f"Reference — {SITE_NAME}",
             "Plain-language reference for Roblox scripting terms.",
             body, depth=1, guides=guides, active_tab="terms/index.html"),
        encoding="utf-8")


def build_index(guides, n_terms=0):
    latest = "".join(row(g) for g in guides[:8])

    picks = []
    for key, meta in SECTIONS.items():
        n = sum(1 for g in guides if g["kind"] == key)
        url = f"{key}s.html" if key == "recipe" else f"{key}.html"
        picks.append(f"""<li><a href="{url}">
      <h3>{meta['title']}</h3>
      <p>{meta['blurb']}</p>
      <p class="pick-meta">{n} {'page' if n == 1 else 'pages'}</p>
    </a></li>""")
    picks.append(f"""<li><a href="terms/index.html">
      <h3>Reference</h3>
      <p>Plain-language entries for the objects, events and properties that come
         up constantly.</p>
      <p class="pick-meta">{n_terms} {'entry' if n_terms == 1 else 'entries'}</p>
    </a></li>""")

    body = f"""<div class="hero">
  <h1>{SITE_NAME}</h1>
  <p class="lede">{SITE_TAGLINE}</p>
</div>
<h2 class="h-label">Start here</h2>
<ul class="picks">{''.join(picks)}</ul>
<h2 class="h-label">Latest</h2>
<ul class="rows">{latest}</ul>
{ad('home-foot')}"""
    (SITE / "index.html").write_text(
        page(f"{SITE_NAME} — Roblox game development reference",
             SITE_TAGLINE, body, guides=guides), encoding="utf-8")


def build_sections(guides):
    for key, meta in SECTIONS.items():
        url = f"{key}s.html" if key == "recipe" else f"{key}.html"
        picked = [g for g in guides if g["kind"] == key]

        groups = []
        for c in CATEGORIES:
            inner = [g for g in picked if g["category"] == c]
            if not inner:
                continue
            groups.append(f'<h2 class="h-label">{icon(c)}{c}</h2>'
                          f'<ul class="rows">{"".join(row(g) for g in inner)}</ul>')

        listing = "".join(groups) or (
            '<p class="empty-note">Nothing here yet. This section is being '
            'written &mdash; try the <a href="index.html">latest guides</a>.</p>')

        body = f"""<div class="page-head">
  <h1>{meta['title']}</h1>
  <p class="lede">{meta['blurb']}</p>
</div>
{listing}
{ad('list-foot')}"""
        (SITE / url).write_text(
            page(f"{meta['title']} — {SITE_NAME}", meta["blurb"], body,
                 active_url=url, guides=guides, active_tab=url),
            encoding="utf-8")


def build_categories(guides):
    out_dir = SITE / "c"
    out_dir.mkdir(parents=True, exist_ok=True)

    for cat in CATEGORIES:
        blurb = CATEGORY_BLURBS.get(cat, "")
        groups = []
        for key, meta in SECTIONS.items():
            inner = [g for g in guides
                     if g["category"] == cat and g["kind"] == key]
            if not inner:
                continue
            groups.append(
                f'<h2 class="h-label">{meta["title"]}</h2>'
                f'<ul class="rows">'
                f'{"".join(row(g, depth=1) for g in inner)}</ul>')

        listing = "".join(groups) or (
            '<p class="empty-note">Nothing here yet. This category is being '
            'written &mdash; try the <a href="../index.html">latest guides</a>, '
            'or <a href="../contribute.html">write the first one</a>.</p>')

        body = f"""<div class="page-head">
  <p class="crumbs"><a href="../index.html">{SITE_SHORT}</a></p>
  <h1>{icon(cat, "h-ico")}{html.escape(cat)}</h1>
  <p class="lede">{html.escape(blurb)}</p>
</div>
{listing}
{ad('list-foot')}"""
        (out_dir / f"{slugify(cat)}.html").write_text(
            page(f"{cat} — {SITE_NAME}", blurb, body, depth=1,
                 active_cat=cat, guides=guides), encoding="utf-8")


def build_pages(guides):
    """About / Contribute / Privacy / Contact. These deliberately carry no ad
    slot -- Google's own guidance discourages ads on policy pages, and they are
    the pages a reviewer reads most carefully."""
    for path in sorted(CONTENT.glob("*.md")):
        meta, md = parse_front_matter(path.read_text(encoding="utf-8"))
        md = re.sub(r"^[ \t]*<!--.*?-->[ \t]*\n?", "", md, flags=re.MULTILINE)
        rendered, _ = render(md)
        title = meta.get("title", path.stem)
        body = f"""<article class="doc">
  <h1>{html.escape(title)}</h1>
  <div class="prose">
{rendered}
  </div>
</article>"""
        (SITE / f"{path.stem}.html").write_text(
            page(f"{title} — {SITE_NAME}", meta.get("description", ""), body,
                 guides=guides), encoding="utf-8")


def build_search_index(guides, glossary=None):
    """Small JSON index; search runs client-side, no backend."""
    items = []
    for g in guides:
        # Whole document, reduced to its unique words. The scorer only asks
        # "does this term appear", so positions and repeats are dead weight --
        # and a word set covers the entire page while staying smaller than a
        # truncated excerpt would be. Substring matching still works, so
        # "invoke" finds "InvokeServer".
        text = html.unescape(strip_tags(g["body"])).lower()
        words = sorted(set(re.findall(r"[a-z0-9_]{2,}", text)))
        items.append({
            "t": g["title"],
            "d": g["description"],
            "u": f"guides/{g['slug']}.html",
            "c": g["category"],
            "k": SECTIONS[g["kind"]]["title"],
            "h": [t for _, t in g["toc"]],
            "b": " ".join(words),
        })
    for term in (glossary or []):
        text = html.unescape(strip_tags(term["body"])).lower()
        words = sorted(set(re.findall(r"[a-z0-9_]{2,}", text)))
        items.append({
            "t": term["term"], "d": term["summary"],
            "u": f"terms/{term['slug']}.html",
            "c": term["category"], "k": "Reference",
            "h": [x for _, x in term["toc"]], "b": " ".join(words),
        })

    for name, title in [("about", "About"), ("contribute", "Contribute"),
                        ("contact", "Contact"), ("privacy", "Privacy")]:
        items.append({"t": title, "d": "", "u": f"{name}.html",
                      "c": "", "k": "Page", "h": [], "b": ""})

    (SITE / "search-index.json").write_text(
        json.dumps(items, separators=(",", ":")), encoding="utf-8")
    return len(items)


def build_sitemap(guides, glossary=None):
    if not SITE_URL:
        return
    urls = ["index.html", "learn.html", "recipes.html", "about.html",
            "contribute.html", "privacy.html", "contact.html"]
    urls += ["terms/index.html"]
    urls += [f"c/{slugify(c)}.html" for c in CATEGORIES]
    urls += [f"guides/{g['slug']}.html" for g in guides]
    urls += [f"terms/{t2['slug']}.html" for t2 in (glossary or [])]
    entries = "".join(f"  <url><loc>{SITE_URL}/{u}</loc></url>\n" for u in urls)
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}</urlset>\n", encoding="utf-8")


def main():
    (SITE / "assets").mkdir(parents=True, exist_ok=True)

    for asset in ("style.css", "search.js"):
        ASSET_V[asset] = asset_version(asset)
    glossary = load_terms(CONTENT, parse_front_matter, render)
    guides = read_guides(glossary)

    for g in guides:
        build_guide(g, guides)
    build_index(guides, len(glossary))
    build_sections(guides)
    build_categories(guides)
    build_terms(glossary, guides)
    build_pages(guides)
    indexed = build_search_index(guides, glossary)
    build_sitemap(guides, glossary)

    for name in ("style.css", "search.js"):
        src = ROOT / "templates" / name
        if src.exists():
            shutil.copy(src, SITE / "assets" / name)

    words = sum(len(strip_tags(g["body"]).split()) for g in guides)
    print(f"built {len(guides)} guides (~{words} words), "
          f"{len(glossary)} reference entries, {indexed} search entries -> docs/")
    if not ADS_ENABLED:
        print("ads: OFF (slots are HTML comments) -- flip ADS_ENABLED after approval")

    if len(guides) < 20:
        print(f"AdSense readiness: {len(guides)}/20 guides minimum.")

    pending = [g["slug"] for g in guides if g["needs_experience"]]
    if pending:
        print(f"\n{len(pending)} guide(s) still need your own first-hand "
              f"paragraph:")
        for slug in pending:
            print(f"  - content/guides/{slug}.md")

    thin = [c for c in CATEGORIES
            if sum(1 for g in guides if g["category"] == c) < 2]
    if thin:
        print(f"\nthin categories (<2 guides): {', '.join(thin)}")


if __name__ == "__main__":
    main()

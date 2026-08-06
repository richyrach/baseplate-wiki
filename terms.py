"""Glossary terms and the Wikipedia-style auto-linker.

A term is a Markdown file in content/terms/ with front matter:

    ---
    term: RemoteEvent
    aka: RemoteEvents
    category: Scripting
    summary: One-line definition shown on hover and in the index.
    ---

    Full explanation...

`link_terms` then turns the FIRST mention of each term in an article into a link
to that term's page. Deliberately conservative: it never touches text inside
code, existing links, or headings, and it caps how many links one page gets --
an article speckled with blue is worse than one with none.
"""

import re

# Never auto-link inside these.
#
# `pre` is the critical one: a link inside a code block would end up in whatever
# the reader copies. Note that inline `<code>` is deliberately NOT protected --
# terms in prose are usually written in backticks, and those are exactly the
# mentions worth linking. Inline code still sits outside `pre`, so the two cases
# separate cleanly.
#
# Headings are excluded so the table of contents and anchors stay plain text.
PROTECTED = {"pre", "a", "h1", "h2", "h3", "h4", "script", "style"}

MAX_LINKS_PER_PAGE = 10


def load_terms(content_dir, parse_front_matter, render):
    """Read content/terms/*.md -> list of term dicts, longest name first."""
    terms = []
    tdir = content_dir / "terms"
    if not tdir.exists():
        return terms

    for path in sorted(tdir.glob("*.md")):
        meta, md = parse_front_matter(path.read_text(encoding="utf-8"))
        md = re.sub(r"^[ \t]*<!--.*?-->[ \t]*\n?", "", md, flags=re.MULTILINE)
        body, toc = render(md)
        name = meta.get("term", path.stem)
        aka = [a.strip() for a in meta.get("aka", "").split(",") if a.strip()]
        terms.append({
            "slug": path.stem,
            "term": name,
            "aka": aka,
            "names": [name] + aka,
            "category": meta.get("category", ""),
            "summary": meta.get("summary", ""),
            "body": body,
            "toc": toc,
        })

    # Longest first so "RemoteFunction" wins before "Remote" can match it.
    terms.sort(key=lambda t: -max(len(n) for n in t["names"]))
    return terms


def _pattern(terms):
    """One alternation of every term name, word-bounded."""
    names = []
    for t in terms:
        for n in t["names"]:
            names.append((n, t))
    names.sort(key=lambda p: -len(p[0]))

    lookup = {}
    parts = []
    for n, t in names:
        key = n.lower()
        if key in lookup:
            continue
        lookup[key] = t
        parts.append(re.escape(n))

    if not parts:
        return None, {}
    return re.compile(r"\b(" + "|".join(parts) + r")\b"), lookup


def link_terms(html_text, terms, current_slug=None, depth=1):
    """Link the first mention of each term. Returns (html, slugs_linked)."""
    pattern, lookup = _pattern(terms)
    if pattern is None:
        return html_text, []

    up = "../" * depth
    used = set()
    stack = []
    out = []
    budget = [MAX_LINKS_PER_PAGE]

    def replace(m):
        word = m.group(1)
        term = lookup.get(word.lower())
        if term is None or budget[0] <= 0:
            return word
        if term["slug"] in used or term["slug"] == current_slug:
            return word
        used.add(term["slug"])
        budget[0] -= 1

        # data-* rather than title=: the native tooltip is slow, unstyleable,
        # and would show on top of our own card.
        summary = (term["summary"].replace("&", "&amp;")
                   .replace('"', "&quot;").replace("<", "&lt;"))
        name = term["term"].replace('"', "&quot;")
        return (f'<a class="term-link" href="{up}terms/{term["slug"]}.html" '
                f'data-term="{name}" data-summary="{summary}">{word}</a>')

    # Walk the HTML, only rewriting text that sits outside protected elements.
    for chunk in re.split(r"(<[^>]+>)", html_text):
        if chunk.startswith("<"):
            tag = re.match(r"</?\s*([a-zA-Z0-9]+)", chunk)
            if tag:
                name = tag.group(1).lower()
                if chunk.startswith("</"):
                    if stack and stack[-1] == name:
                        stack.pop()
                elif not chunk.endswith("/>") and name in PROTECTED:
                    stack.append(name)
            out.append(chunk)
        elif stack:
            out.append(chunk)          # inside protected element, leave alone
        else:
            out.append(pattern.sub(replace, chunk))

    return "".join(out), sorted(used)

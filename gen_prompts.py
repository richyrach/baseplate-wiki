#!/usr/bin/env python3
"""Regenerate TOPICS.md and CHATGPT-ALL-PROMPTS.md from topics.py.

    python3 gen_prompts.py

The prompt body is lifted out of CHATGPT-BRIEF.md so the two files cannot drift
apart -- edit the rules there, regenerate here.
"""

import re
from collections import Counter
from pathlib import Path

from build import CATEGORIES
from topics import TOPICS

ROOT = Path(__file__).parent


def slug(text, words=6):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return "-".join(s.split("-")[:words])


def check():
    """Every category needs >=2 topics or its page ships thin."""
    counts = Counter(c for _, c, _, _, _ in TOPICS)
    problems = []
    for c in CATEGORIES:
        if counts[c] < 2:
            problems.append(f"{c} has {counts[c]}")
    unknown = set(counts) - set(CATEGORIES)
    if unknown:
        problems.append(f"unknown categories: {', '.join(sorted(unknown))}")
    return problems, counts


def write_topics(counts):
    done = sum(1 for *_, d in TOPICS if d)
    lines = [
        "# The guide plan",
        "",
        f"{len(TOPICS)} guides, {done} written. Generated from `topics.py` -- edit "
        "that file and run `python3 gen_prompts.py` rather than editing this one.",
        "",
        "Every category has at least two published guides, so no section of the "
        "nav leads to an empty page. Remaining topics can be written in any "
        "order — pick whichever you have actually hit recently, since that is "
        "where your own notes will be freshest.",
        "",
    ]
    n = 0
    for cat in CATEGORIES:
        lines.append(f"## {cat} ({counts[cat]})")
        lines.append("")
        for topic, c, kind, level, is_done in TOPICS:
            if c != cat:
                continue
            n_idx = [i for i, t in enumerate(TOPICS, 1) if t[0] == topic][0]
            mark = "x" if is_done else " "
            lines.append(f"- [{mark}] {n_idx:02d} — {topic}  \n      `{kind}` · `{level}`")
        lines.append("")
    (ROOT / "TOPICS.md").write_text("\n".join(lines), encoding="utf-8")


def write_prompts():
    # CHATGPT-BRIEF.md is a local working file and is not in the public repo.
    # Without it we still regenerate TOPICS.md; only the prompt pack is skipped.
    brief_path = ROOT / "CHATGPT-BRIEF.md"
    if not brief_path.exists():
        return None

    brief = brief_path.read_text(encoding="utf-8")
    # Explicit markers -- splitting on "---" collided with the YAML fences
    # inside the prompt and silently truncated every job.
    try:
        core = brief.split("<!-- PROMPT-START -->", 1)[1]
        core = core.split("<!-- PROMPT-END -->", 1)[0].strip()
    except IndexError:
        raise SystemExit("CHATGPT-BRIEF.md is missing the PROMPT-START/END markers")
    if "TOPIC: <TOPIC>" not in core:
        raise SystemExit("prompt core lost its TOPIC placeholder -- check the brief")

    pending = [(i, t, c, k, l)
               for i, (t, c, k, l, d) in enumerate(TOPICS, 1) if not d]

    out = [f"""# All {len(pending)} remaining prompts, topics pre-filled

Hand this whole file to ChatGPT with this instruction:

> Below are {len(pending)} separate writing jobs. Do NOT write them all at once.
> Write job {pending[0][0]:02d} only, in full. When I reply "next", write the
> following job. Continue one at a time. Follow the rules in each job exactly,
> including the front matter block and the `<!-- OWN_EXPERIENCE -->` marker.

Then paste each reply back to me and I'll add it to the site. Keep the suggested
filenames -- the slugs are already search-shaped.

Generated from `topics.py`. Guides already written are skipped.
"""]

    for num, topic, cat, kind, level in pending:
        out.append(f"""
---

## Job {num:02d} — {cat}

Suggested filename: `content/guides/{slug(topic)}.md`
Front matter must use exactly: `category: {cat}`, `kind: {kind}`, `level: {level}`

{core.replace('TOPIC: <TOPIC>', f'TOPIC: {topic}')}
""")

    (ROOT / "CHATGPT-ALL-PROMPTS.md").write_text("\n".join(out), encoding="utf-8")
    return len(pending)


if __name__ == "__main__":
    problems, counts = check()
    write_topics(counts)
    pending = write_prompts()
    if pending is None:
        print(f"{len(TOPICS)} topics across {len(counts)} categories; "
              f"TOPICS.md written (no local brief, prompt pack skipped)")
    else:
        print(f"{len(TOPICS)} topics across {len(counts)} categories; "
              f"{pending} prompts written")
    if problems:
        print("thin plan: " + "; ".join(problems))
    else:
        print("every category has at least 2 planned guides")

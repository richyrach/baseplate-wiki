# Baseplate Wiki

An open reference for Roblox game development — written and tested by hand, and
open to corrections.

**Live site:** _(GitHub Pages URL goes here once enabled)_

- **Learn** — explanations you read once, in order, to understand how something works.
- **Recipes** — self-contained answers to one specific task.
- **Reference** — plain-language entries for the objects, events and properties that
  come up constantly.

## Contributing

Corrections are genuinely welcome — Roblox changes constantly and a guide that was
right six months ago may quietly not be any more.

1. Edit the relevant Markdown file under `content/`.
2. Run `python3 build.py`.
3. Open a pull request describing what you changed and why.

You do not need to know git to help. Reporting a mistake by email is just as useful:
see the site's Contribute page.

### The standard for a guide here

- **The code has been run.** Not "should work" — actually pasted into Studio.
- **Errors are quoted exactly** as Roblox prints them.
- **It says when it doesn't know.** Version-dependent behaviour is flagged, not
  papered over.

## Building

No dependencies beyond Python 3. No npm, no build tools.

```bash
python3 build.py
```

Markdown in `content/` becomes HTML in `site/`. Edit `templates/style.css`, never
anything inside `site/` — that directory is regenerated on every build.

| File | Purpose |
|---|---|
| `build.py` | site generator |
| `luau.py` | build-time Luau syntax highlighter |
| `terms.py` | glossary loading and the auto-linker |
| `topics.py` | the guide plan, as data |
| `gen_prompts.py` | regenerates `TOPICS.md` from `topics.py` |

## Licence

Content is published so people can learn from it. Code samples in the guides are free
to use in your own games without attribution.

Not affiliated with or endorsed by Roblox Corporation.

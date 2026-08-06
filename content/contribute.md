---
title: Contribute to Baseplate Wiki
description: How to correct a guide, add a missing one, or become an editor. Every page here is open to correction.
---

Baseplate Wiki is open to correction. Roblox changes constantly, and a guide that
was accurate when it was written can quietly stop being accurate six months later.
If you find something wrong, I would genuinely rather know than keep a tidy site.

There are three ways in, in rough order of how much effort they take.

## 1. Just tell me (easiest)

Email `richyrachfansgmial@gmail.com` with the guide name and what's wrong. You do
not need a GitHub account, you do not need to know git, and you do not need to
write the fix yourself — "the code in section 3 errors on line 2" is a completely
useful message.

To make a correction fast to verify, it helps if you include:

- which guide, and roughly which section
- what you expected to happen
- the exact error text, if there was one
- your Roblox Studio version, if the guide touches a recent API

## 2. Send an edit (for anything substantial)

Every page on this site is a Markdown file in a public git repository. You can
propose a change the same way you would to any open source project:

1. Fork the repository.
2. Edit the `.md` file for the guide under `content/guides/`.
3. Open a pull request describing what you changed and why.

I review every pull request myself. Nothing goes live without being read first,
which is deliberate — see *Why this is not an open wiki* below.

You don't need to build the site to contribute. If your Markdown is valid, it will
render. If you do want to check it locally, it's one command and needs nothing but
Python:

```bash
python3 build.py
```

## 3. Become an editor

If you send a few good corrections, or write a guide that gets published, I will
add you to the repository as a reviewer. Editors get their name on the guides they
wrote, and can approve other people's corrections.

There is no application form and no minimum. Send one useful thing and you're
effectively already in.

## What makes a guide publishable here

The standard is narrow on purpose, and it is the reason this site exists at all:

- **The code has been run.** Not "should work" — actually pasted into Studio and
  executed. If it has a caveat, the guide says so.
- **Errors are quoted exactly** as Roblox prints them. Searching the literal error
  string is how most readers arrive at a page.
- **It says when it doesn't know.** Where behaviour is version-dependent, or only
  one path was tested, that is stated rather than papered over.
- **It contains something first-hand.** The hours you lost, the wrong guess you
  made first, the number you measured. A guide that could have been assembled
  without touching Studio is not useful to anyone.

That last point is the one I hold hardest. There is already an enormous amount of
generic, confidently-wrong Roblox content online. This site is meant to be the
other thing.

## Why this is not an open wiki

The name says wiki and the contribution model is real, but there is no "edit this
page" button that publishes instantly, and that is a considered decision rather
than laziness:

- **Every change gets read.** An unreviewed edit on a technical guide can put code
  in front of a beginner that silently corrupts their save data. Review is cheap
  and the alternative is not.
- **Spam.** Open-edit sites with any traffic attract link spam within days, and
  fighting it is a full-time job I do not have.
- **Attribution stays clean.** Pull requests carry a permanent, public record of
  who wrote what.

Reviewed contribution gets essentially all the value of an open wiki without the
failure modes. If this site ever grows enough to need real editor accounts, that
will be a good problem to have, and it can be built then.

## Reporting something other than a mistake

- **Guide requests** — tell me what you're stuck on. A specific stuck problem is
  far more useful to me than a broad topic suggestion; being stuck is the origin of
  every guide here.
- **Roblox account problems** (bans, purchases, Robux) — only Roblox Support can
  help. This site has no connection to Roblox Corporation.
- **Exploits, or scripts meant to break other people's games** — not welcome here,
  and pull requests adding them will be closed.

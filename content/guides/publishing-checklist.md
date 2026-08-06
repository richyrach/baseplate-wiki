---
title: "The publishing checklist people forget before release"
description: The settings that are off by default and quietly break DataStores, badges, purchases and mobile play once you publish.
date: 2026-08-06
category: Performance
kind: recipe
level: Beginner
minutes: 8
---

Your game works in Studio. Several things that work in Studio do not work in a
published game until you turn them on, and each one fails in its own confusing way.

Go through this before telling anyone to play.

## Settings that break things silently

### Studio Access to API Services

**Home → Game Settings → Security → Enable Studio Access to API Services**

Without it, every DataStore call fails **in Studio**. People turn this on, get
DataStores working in Studio, and forget that it only ever affected Studio — a
published game can always use DataStores.

The inverse trap is more common: testing in Studio with this off, concluding
DataStores are broken, and rewriting working code.

### Allow HTTP Requests

**Game Settings → Security → Allow HTTP Requests**

Needed for `HttpService`. Off by default. If you are using any external API or
webhook, this is why it returns an error about HTTP requests not being enabled.

### Third-party sales and teleports

Under the same Security section:

- **Allow Third Party Sales** — needed to sell items you do not own.
- **Allow Third Party Teleports** — needed to teleport players to a place you do not
  own.

Both off by default, both fail with a permissions error that does not obviously point
at a setting.

## Avatar and rig

**Game Settings → Avatar**

Pick R6 or R15 deliberately. If your animations were authored for one rig and the
game is set to the other, they will not play correctly — and the symptom is silence,
not an error.

Also check the avatar scaling settings if your map has tight spaces. Default settings
allow a range of body sizes, and a doorway that fits your avatar may not fit
everyone's.

## Streaming

**Game Settings → World → Streaming Enabled**

Streaming loads only nearby parts on each client. It is a large performance win for
big maps and it **will** break code that assumes every part exists:

```lua
-- may be nil on a client with streaming on
local part = workspace.FarAwayThing
```

If you turn it on, audit every client-side reference into `Workspace` for
`WaitForChild` with a timeout and a `nil` check. Turning streaming on the day before
release is how you ship a game full of intermittent client errors.

Decide early and test with it on for a while.

## Playable devices

**Game Settings → Basic Info → Playable Devices**

Every device is ticked by default. If your game genuinely does not work on phones —
no touch controls, unreadable UI — untick them rather than shipping a bad experience
that collects one-star ratings.

If you do support phones, actually test in the device emulator first. See the UI
guides on Offset sizing and touch input, which cause most mobile failures.

## Before you publish

### Check the Developer Console on both sides

Join your own game, press `F9`, and read **both** the Client and Server tabs. A red
error you have never seen because you only looked at the Studio output is the classic
launch-day surprise.

### Test with more than one client

**Test tab → Clients: 2 → Start.** This runs a real server process and two real
client processes. Client-server bugs that are invisible in single-player Play mode
show up here immediately.

### Confirm data actually saves

1. Join the published game, not Studio.
2. Change something that should persist.
3. Leave properly, by closing the client.
4. Rejoin and check.

Step 3 matters — stopping a Studio playtest does not run `game:BindToClose`, so
shutdown saving is untested in Studio by definition.

### Count your parts and check what is anchored

```lua
local total, unanchored = 0, 0
for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("BasePart") then
		total += 1
		if not d.Anchored then unanchored += 1 end
	end
end
print(total, "parts,", unanchored, "unanchored")
```

Static scenery that is not anchored is both a physics cost and a visual bug waiting
to happen.

### Remove your debug output

Search for `print(` and decide about each one. Anything in a per-frame loop should
go. Remember that players can open `F9` and read everything you print — including
anything that hints at how your anti-exploit checks work.

## Store page basics

- **Icon and thumbnails.** These are most of whether anyone clicks. A screenshot of
  actual gameplay beats a render.
- **Description.** Say what the player does. Plainly.
- **Genre**, so it appears in the right places.

## After publishing

Set the place's version live properly: **File → Publish to Roblox**, then check in
the Creator Dashboard that the version you expect is the one serving. Publishing a
place is not the same as making that version current if you have used version
history.

> [!note]
> Roblox caches assets aggressively. If a change does not appear immediately in the
> live game, that is usually normal propagation rather than a failed publish. Check
> the version in the dashboard before re-publishing repeatedly.

<!-- OWN_EXPERIENCE -->

## The short version

1. API Services on, if you want DataStores working in Studio.
2. HTTP Requests on, if you use `HttpService`.
3. Avatar rig matches your animations.
4. Streaming decided early, and audited if on.
5. Playable devices match reality.
6. Two-client test passes.
7. Both `F9` tabs clean.
8. Save/rejoin verified in the **live** game.
9. Static parts anchored.
10. Debug prints removed.

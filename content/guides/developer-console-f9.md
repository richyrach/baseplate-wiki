---
title: "The Developer Console (F9): finding the errors Studio never showed you"
description: Client errors in a live game do not appear in the Studio output window. This is where they go, and how to read them.
date: 2026-08-06
category: Scripting
kind: learn
level: Beginner
minutes: 7
---

You publish the game, join it, and something is broken. You alt-tab to Studio and
the output window is empty and clean.

The output window is not lying to you. It simply is not connected to the game you
are playing. In a live game, the error you are looking for is almost always in the
**Developer Console**, and you open it by pressing `F9`.

A large share of "there's no error, it just doesn't work" turns out to be a red
line sitting in a console that has never been opened.

## Opening it

- **Computer:** press `F9` while in the game.
- **In-game menu:** Escape → Settings, then the console option.
- **Chat command:** type `/console`.
- **Phone or tablet:** the chat command is the only reliable route.

It works in a live game and in Studio, and it is available to any player, not just
the game's owner. That last part matters both ways: it is how a player can send
you a useful bug report, and it is a reminder that anything you `print` is visible
to anyone who looks.

## The part people miss: client and server are separate

At the top of the console there is a switch between **Client** and **Server**.
They are different logs and neither shows the other's messages.

- **Client** — everything from LocalScripts on your own machine.
- **Server** — everything from server Scripts, for the whole server.

If you are hunting a bug and the log looks empty, check that you are on the right
side first. It is the single most common reason people conclude "there is no
error."

> [!note]
> In a live game you only see the **server** log for a game you have edit
> permissions on. Ordinary players see their own client log only. That is a
> privacy and security boundary, not a bug.

## Reading a stack trace

A red error looks roughly like this:

```text
MainMenu is not a valid member of PlayerGui "Players.You.PlayerGui"
  Stack Begin
  Script 'Players.You.PlayerGui.MenuHandler', Line 4
  Stack End
```

Read it from the top:

- **Line 1** is what went wrong.
- The `Script '...'` line is the full path to the script, so you know exactly
  which file to open — useful when you have three scripts with similar names.
- **Line 4** is where it happened.

When there are several `Script` lines, they are the call chain. The top one is
where the error occurred; the ones below are what called it. If the top line is
inside a module you did not write, the interesting line is usually the first one
that *is* yours.

## Colours

- **Red** — an error. Execution of that thread stopped.
- **Orange or yellow** — a `warn()`, or a Roblox deprecation notice. Not fatal,
  often still worth reading.
- **White or grey** — `print()` output.
- **Blue-ish info lines** — Roblox's own engine messages.

The deprecation warnings are worth a look every so often. They are how you find
out that a function you are relying on is scheduled to stop working.

## Making your own output easier to find

Once a game has any real traffic, the console fills with noise. Two habits make
your own messages findable.

**Tag them.** Pick a prefix per system:

```lua
print("[Vehicles] spawned", model.Name, "for", player.Name)
warn("[Vehicles] no spawn point found, using origin")
```

Then use the console's filter box to type `[Vehicles]` and see only that system.

**Use `warn` for things you want to notice.** It comes out coloured, so it stands
out from ordinary prints:

```lua
if not spawnPoint then
	warn("[Vehicles] SpawnPoint missing -- add one to Workspace")
	return
end
```

## The other tabs

The console has more than a log. Two are genuinely useful:

- **Memory** — memory use broken down by category. This is where you look when a
  game gets slower the longer a server stays up, which usually means something is
  being created and never destroyed.
- **Network** — data being sent. Worth a look if you suspect a RemoteEvent is
  firing far more often than you intended, which is a common cause of lag that
  looks like a rendering problem.

There is also the **MicroProfiler** (`Ctrl+F6`), which is a separate and much
deeper tool for frame-time analysis.

<!-- OWN_EXPERIENCE -->

## Before you ask anyone for help

If you are about to post in a forum or a Discord asking why something is broken,
do these four things first. They resolve a surprising fraction of problems on
their own, and they make the question answerable if not:

1. Open `F9` and switch to the correct side, client or server.
2. Copy the **entire** red block, including the `Stack Begin`/`Stack End` lines.
   The script path and line number are the parts that let someone actually help.
3. Add `print("reached line N")` above the failing line and confirm the code even
   gets there. Quite often it does not, and the real bug is earlier.
4. Check whether it happens in Studio with **two** test clients, not just
   single-player Play. If it only breaks live, the cause is usually a client-server
   or replication-timing issue rather than your logic.

---
title: Your script works in Studio but breaks in the real game. Here's why.
description: Studio runs the server and client in one process, so client-server bugs stay invisible until you publish. The five that catch everyone, and how to catch them before players do.
date: 2026-08-05
category: Scripting
kind: learn
level: Beginner
minutes: 9
---

You test in Studio. Everything works. You publish, join the live game, and the
thing you just spent two hours on does nothing at all — no error, no output, just
silence.

This is the single most common wall new Roblox developers hit, and it is almost
never a bug in your logic. It is that **Studio lies to you about where your code
is running.**

## Why Studio lies

When you press Play in Studio, Roblox runs the server and your client in the same
process on your machine. They share memory. They start at the same instant. A
`LocalScript` and a `Script` in Studio are neighbours; in a live game they are on
different computers, possibly in different countries, talking over a network with
real latency.

So in Studio, sloppy code that reaches across the client-server boundary appears
to work — because there is no boundary to cross yet.

> [!note]
> The fastest fix for this entire class of bug: in Studio, open the **Test** tab
> and set clients to 2, then click **Start**. That launches a real server process
> and two real client processes. Most of the bugs below surface immediately.

## 1. LocalScripts that aren't running at all

A `LocalScript` only runs in a handful of places:

- inside a player's `Backpack` (tools)
- inside `StarterPlayerScripts` or `StarterCharacterScripts`
- inside `PlayerGui`
- inside the player's `Character`

Put a `LocalScript` in `Workspace`, `ServerScriptService`, or `ReplicatedStorage`
and it will simply never execute. No error. No warning. Silence.

In Studio's single-process Play mode you may have gotten away with a script in
the wrong place because you *also* had a working copy somewhere else. In the live
game, silence.

**Check:** put a `print("alive")` as line 1 of every script that "isn't working."
If you don't see it in the output, the script never ran and nothing after line 1
matters.

## 2. Waiting for things that don't exist yet

This is the big one. In Studio, everything loads instantly. In the live game,
your client starts running scripts while assets are still streaming in.

```lua
-- Breaks in the live game, works in Studio
local gui = game.Players.LocalPlayer.PlayerGui.MainMenu
local button = gui.PlayButton
```

If `MainMenu` hasn't replicated to the client yet, that first line throws
`MainMenu is not a valid member of PlayerGui`. Written the safe way:

```lua
local Players = game:GetService("Players")
local player = Players.LocalPlayer

local gui = player:WaitForChild("PlayerGui"):WaitForChild("MainMenu")
local button = gui:WaitForChild("PlayButton")
```

`WaitForChild` yields until the child appears instead of erroring on a race.

> [!warning]
> `WaitForChild` with no timeout waits forever, which turns a crash into a hang —
> harder to debug, not easier. Pass a timeout and handle the miss:
> `local gui = player:WaitForChild("MainMenu", 10) if not gui then warn("MainMenu never arrived") return end`

Use `WaitForChild` on the **client** for things the server created. You generally
do *not* need it on the server for things that exist in the published place file.

## 3. Trusting the client with anything that matters

A `LocalScript` runs on the player's machine. The player controls that machine.
Anything you calculate there, an exploiter can change.

```lua
-- LocalScript: an exploiter can set this to whatever they want
local coins = 0
local function onCoinTouched()
    coins += 1
    coinsChanged:FireServer(coins)   -- server believes a number from the client
end
```

The server must own every value that matters — currency, health, inventory,
scores. The client's job is to *ask*, and the server's job is to *decide*:

```lua
-- ServerScriptService
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local collectCoin = ReplicatedStorage:WaitForChild("CollectCoin")

local balances = {}

collectCoin.OnServerEvent:Connect(function(player, coinId)
    local coin = workspace.Coins:FindFirstChild(coinId)
    if not coin then return end

    -- the server checks the claim itself
    local character = player.Character
    if not character or not character.PrimaryPart then return end
    if (character.PrimaryPart.Position - coin.Position).Magnitude > 12 then
        return
    end

    coin:Destroy()
    balances[player.UserId] = (balances[player.UserId] or 0) + 1
end)
```

Note the shape: the client sends *which coin*, never *how many coins I now have*.
Every `OnServerEvent` handler receives `player` as its first argument
automatically, and that argument is the one thing on the whole call you can
actually trust — Roblox fills it in, not the client.

## 4. Changes on the client that never reach anyone else

If a `LocalScript` moves a part, changes a colour, or deletes something in
`Workspace`, only that one player sees it. It does not replicate upward. In
Studio's shared process this distinction blurs and it can look like it worked.

```lua
-- LocalScript: only this player ever sees the door open
workspace.Door.CFrame = workspace.Door.CFrame * CFrame.Angles(0, math.rad(90), 0)
```

If every player should see it, the **server** has to do it. Fire a RemoteEvent to
the server and let the server make the change.

The reverse also holds and is genuinely useful: client-only changes are how you
build things like a local preview or a per-player highlight without touching
anyone else's game.

## 5. RemoteEvents connected on the wrong side

The naming is symmetrical and easy to get backwards:

| You want | Client calls | Server listens |
|---|---|---|
| client tells server | `:FireServer(...)` | `.OnServerEvent` |
| server tells client | `.OnClientEvent` | `:FireClient(player, ...)` |

Connecting `OnServerEvent` inside a `LocalScript` produces no error. It just
never fires. Same in reverse. If a remote "isn't working," check which script
type each half lives in before you check anything else.

## A checklist before you publish

1. Test with 2 clients from the **Test** tab, not single-player Play.
2. Add `print` at the top of each script — confirm it actually runs.
3. Every client-side reference to a server-made object uses `WaitForChild` with a
   timeout.
4. No `FireServer` sends a value the server could compute itself.
5. Open the **Developer Console** in the live game with `F9` — client errors show
   up there and *never* appear in your Studio output.

That last one matters more than it sounds. Most "it works in Studio" reports are
really "there is a red error in the live client console that I have never
looked at."

> [!note]
> **From my own build:** on my traffic game the AI cars drove fine in Studio and
> spawned inside each other in the live game. Cause was #2 — the spawn script read
> `workspace.Nodes` before the node folder finished replicating, got `nil` for
> half the nodes, and defaulted every one of them to the origin. `WaitForChild`
> on the folder fixed it in one line.

## What to read next

The client-server split is the foundation everything else sits on. Once it clicks,
RemoteFunctions, DataStores, and anti-exploit work all get considerably less
mysterious — they are all the same boundary seen from different angles.

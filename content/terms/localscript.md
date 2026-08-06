---
term: LocalScript
aka: LocalScripts
category: Scripting
summary: A script that runs on one player's own device, not on the server. Only runs in a few specific places.
---

A `LocalScript` runs on a single player's machine. Whatever it does, it does only
for that player, and the player's own computer is doing the work.

That has two consequences that cause most of the confusion around it: a
LocalScript only runs in certain locations, and nothing it decides can be
trusted.

## Where it actually runs

A `LocalScript` executes **only** if it ends up inside one of these:

- `StarterPlayer > StarterPlayerScripts` — runs once when the player joins
- `StarterPlayer > StarterCharacterScripts` — runs each time their character spawns
- the player's `PlayerGui` (usually via `StarterGui`)
- the player's `Backpack` (usually via `StarterPack`) — tools
- the player's `Character` model

Put one in `Workspace`, `ServerScriptService`, `ReplicatedStorage`, or
`ServerStorage` and it does nothing at all. There is no error and no warning in
the output. It simply never starts.

> [!note]
> `StarterGui`, `StarterPack` and `StarterPlayerScripts` are templates. Their
> contents get **copied** into each player when they join. The copy is what runs,
> which is why editing the original mid-game does not affect players already in
> the server.

## What it can and cannot see

A LocalScript can read `game.Players.LocalPlayer`. A server `Script` cannot —
`LocalPlayer` is `nil` on the server, because a server has many players and no
single "local" one.

Going the other way, a LocalScript cannot see anything in `ServerStorage` or
`ServerScriptService`. Those never replicate to clients. If both sides need
something, it goes in `ReplicatedStorage`.

## Changes it makes are private

If a LocalScript moves a part, recolours it, or deletes it, **only that player
sees the change.** It does not travel back to the server or to anyone else.

```lua
-- LocalScript: only this one player sees the door swing open
workspace.Door.CFrame = workspace.Door.CFrame * CFrame.Angles(0, math.rad(90), 0)
```

This is often the bug. It is also occasionally exactly what you want — a preview,
a personal highlight, a client-only effect.

To change something everyone sees, the server has to do it. Send a request with a
RemoteEvent and let the server make the change.

## Nothing it says can be trusted

The player controls their own device, so they can modify anything a LocalScript
computes. Exploiters routinely do.

That means a LocalScript may **ask**, but the server must **decide**:

```lua
-- Wrong: the client tells the server how much it earned
coinsEarned:FireServer(9999)

-- Right: the client reports what it did, the server works out the reward
coinPickedUp:FireServer(coinId)
```

Anything that affects currency, health, inventory, progress, or another player
has to be validated on the server, every time, no exceptions.

## What it is good at

None of the above makes LocalScripts second-class. They are the right tool for
everything that is about *this* player's experience:

- reading input (`UserInputService`, `ContextActionService`)
- driving the interface in `PlayerGui`
- camera work
- immediate visual and audio feedback, so an action feels instant instead of
  waiting for a network round trip
- anything running every frame via `RunService.RenderStepped`

The usual shape of a responsive game is: the client shows the effect right away,
fires a RemoteEvent, and the server decides what actually happened.

## Telling whether it ran at all

Before debugging the logic, confirm it started:

```lua
print("LocalScript alive:", script:GetFullName())
```

Client output does not appear in the Studio output window when you are testing a
live game — open the **Developer Console** with `F9` in the running game to see
it. A large share of "my LocalScript is broken" turns out to be "it never ran
because it was in the wrong place."

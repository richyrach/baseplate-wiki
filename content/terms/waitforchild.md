---
term: WaitForChild
aka: WaitForChild()
category: Scripting
summary: Pauses until a named child exists, instead of erroring because it has not replicated yet.
---

`WaitForChild` looks for a child by name and yields until it appears, rather than
erroring immediately when it is not there yet.

```lua
local gui = player:WaitForChild("PlayerGui"):WaitForChild("MainMenu")
```

It exists because of replication timing. In Studio everything is present
instantly, so direct indexing appears to work. In a live game the client starts
running scripts while objects are still arriving from the server, and direct
indexing throws:

`MainMenu is not a valid member of PlayerGui`

## Always pass a timeout

With no second argument, `WaitForChild` waits **forever**. If the object never
arrives, the script hangs silently — which is harder to debug than the error you
were trying to avoid, because there is nothing in the output at all.

```lua
local menu = player.PlayerGui:WaitForChild("MainMenu", 10)
if not menu then
    warn("MainMenu never arrived")
    return
end
```

With a timeout it returns `nil` on failure, so you can handle it.

> [!warning]
> A `WaitForChild` with no timeout inside a loop that runs per player, or on a
> Touched event, can leave threads parked indefinitely. Every one of them holds
> its captured variables in memory.

## Where you need it, and where you do not

Use it **on the client**, for anything the server created or that streams in.

You usually do **not** need it on the server for objects that already exist in
the published place file — the server has the whole data model from the moment it
starts. Wrapping every server-side lookup in `WaitForChild` is a common habit that
adds noise and can mask a genuine typo, because a misspelled name now hangs
instead of erroring.

## The alternatives

- `FindFirstChild(name)` — returns `nil` immediately, never waits. Right when the
  object is optional and you want to branch on its absence.
- `ChildAdded` — an event, for reacting to things that appear later.
- Direct indexing (`parent.Name`) — fine for objects you are certain exist right
  now, and it fails loudly if you are wrong, which is sometimes what you want.

The rule of thumb: `WaitForChild` when it *will* exist and you need to wait,
`FindFirstChild` when it *might not* exist and you need to check.

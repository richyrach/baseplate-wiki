---
term: ReplicatedStorage
category: Scripting
summary: The container both the server and every client can see. Where shared assets and RemoteEvents live.
---

`ReplicatedStorage` is a service whose contents are visible to **both** the server
and every client. That is the whole point of it, and it is why RemoteEvents and
RemoteFunctions normally live there — both halves of the conversation need to find
the same object.

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local remotes = ReplicatedStorage:WaitForChild("Remotes")
local equipItem = remotes:WaitForChild("EquipItem")
```

A typical layout:

```text
ReplicatedStorage
├── Remotes
│   ├── EquipItem
│   └── GetInventory
├── Modules
│   └── ItemConfig
└── Assets
    └── CoinModel
```

## What belongs here

- RemoteEvents and RemoteFunctions
- ModuleScripts both sides need — shared config, shared maths
- models the client needs to clone for previews or effects

## What does not

Anything the player should not be able to read. Contents of
`ReplicatedStorage` are fully visible to clients, and an exploiter can read every
value in it. It is *shared*, not *secret*.

> [!warning]
> Putting a table of item prices, drop rates, or admin user IDs in
> ReplicatedStorage means players can read all of it. That is fine for prices you
> display anyway; it is not fine for anything that is meant to be hidden or
> authoritative. Use `ServerStorage` or `ServerScriptService` for those.

## The sibling containers

| Container | Server sees | Client sees |
|---|---|---|
| `ReplicatedStorage` | yes | yes |
| `ServerStorage` | yes | no |
| `ServerScriptService` | yes | no |
| `Workspace` | yes | yes |

Objects in `ReplicatedStorage` are not in the world, so they do not render, do not
collide, and cost nothing to have sitting there. That makes it the normal home for
things you will `:Clone()` into `Workspace` later.

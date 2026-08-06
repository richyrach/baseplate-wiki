---
term: RemoteEvent
aka: RemoteEvents
category: Scripting
summary: One-way messaging across the client-server boundary. Fires and returns immediately without waiting for a reply.
---

A `RemoteEvent` sends a message between the server and a client and continues
immediately. It returns nothing.

It normally lives in `ReplicatedStorage`, because both sides need to be able to find
the same object.

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local remote = ReplicatedStorage:WaitForChild("Remotes"):WaitForChild("EquipItem")
```

## The four calls

| Direction | Sender calls | Receiver connects |
|---|---|---|
| client → server | `:FireServer(...)` | `.OnServerEvent` |
| server → one client | `:FireClient(player, ...)` | `.OnClientEvent` |
| server → everyone | `:FireAllClients(...)` | `.OnClientEvent` |

Connecting `OnServerEvent` in a LocalScript produces no error and never fires. Same
in reverse. When a remote "does nothing," check which script type each half is in
before checking anything else.

## The player argument is added for you

`OnServerEvent` receives the firing player as its **first** argument, inserted by
Roblox:

```lua
remote.OnServerEvent:Connect(function(player, itemName)
	-- player is trustworthy; itemName is not
end)
```

The client does not send it, and should not:

```lua
remote:FireServer(game.Players.LocalPlayer, "Sword")   -- wrong, sends it twice
remote:FireServer("Sword")                             -- right
```

That `player` argument is the one value in the whole call you can trust, because the
engine filled it in rather than the client.

## Everything else is untrusted

Any client can fire any remote with any arguments, at any rate. A player does not need
to modify your code to do it.

So every handler needs, in roughly this order:

```lua
remote.OnServerEvent:Connect(function(player, itemName)
	if rateLimited(player) then return end              -- 1. how often
	if typeof(itemName) ~= "string" then return end      -- 2. what type
	if not allowedItems[itemName] then return end        -- 3. is it real
	-- 4. is this player allowed to, and near enough to, do this
end)
```

The design rule that matters more than any individual check: the client sends
**identifiers**, never **values**. `FireServer(coinPart)` is fine; `FireServer(500)`
where 500 is a coin amount is a free money exploit no validation can fix.

## Rate limiting is not optional

`FireServer` can be called thousands of times a second. Without a limit, a single
player can pin your server's CPU using a handler that is otherwise completely correct.

```lua
local lastCall = {}

local function rateLimited(player)
	local now = os.clock()
	local last = lastCall[player.UserId]
	if last and now - last < 0.1 then
		return true
	end
	lastCall[player.UserId] = now
	return false
end
```

Clear the entry on `PlayerRemoving` or the table grows for the life of the server.

## When not to use one

**When you need an answer** — use a `RemoteFunction`, or fire a second RemoteEvent
back with the result. `FireServer` returns nothing; assigning its result gives you
`nil`.

**For state that should just be readable** — a `Value` object or an attribute
replicates automatically and is available to players who join later. A RemoteEvent
only reaches whoever was connected when it fired, which is why late joiners see a
blank scoreboard.

**Every frame** — `FireAllClients` in a `Heartbeat` loop is 60 messages per player per
second. Send less often, or use a replicated property.

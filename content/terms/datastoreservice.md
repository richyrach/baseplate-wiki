---
term: DataStoreService
category: Data
summary: Persistent storage across sessions. Every call is a network request that can fail, and there is a per-minute budget.
---

`DataStoreService` is how data survives a player leaving. It is server-only, every
call goes over the network, and every call can fail.

```lua
local DataStoreService = game:GetService("DataStoreService")
local store = DataStoreService:GetDataStore("PlayerData_v1")

local ok, data = pcall(function()
	return store:GetAsync(player.UserId)
end)
```

`GetDataStore` itself does not touch the network — it just names a store. The
`Async` calls are the ones that can fail.

## Two things to do before anything works

**Enable API access for Studio:** Home → Game Settings → Security → *Enable Studio
Access to API Services*. Without it every call fails in Studio, and the error message
about API services is easy to mistake for a code problem.

**Publish the place.** DataStores do not work in an unpublished place at all.

## pcall is mandatory

Not defensive style — mandatory. An unprotected `GetAsync` that fails throws, so the
rest of your load function never runs. The player then gets default values, and when
they leave, those defaults are saved over their real data.

That failure chain is the single most destructive bug in Roblox data handling, and the
fix is to treat a failed load as a reason to **disable saving** for that session:

```lua
local ok, result = pcall(function() return store:GetAsync(userId) end)

if not ok then
	dataFailed[userId] = true      -- refuse to save later
	return defaults()
end
```

## SetAsync vs UpdateAsync

```lua
store:SetAsync(userId, data)                     -- overwrite

store:UpdateAsync(userId, function(old)          -- read and write atomically
	local d = old or { Coins = 0 }
	d.Coins += 50
	return d
end)
```

Use `UpdateAsync` whenever the new value depends on the old one. With `SetAsync`, two
servers can both read 100, both add 50, and both write 150 — losing one increment.
`UpdateAsync` cannot lose that way.

> [!warning]
> The callback you pass to `UpdateAsync` must not yield. No `task.wait`, no nested
> DataStore calls, no `WaitForChild`. Compute and return.

## The request budget

Each server has an allowance per minute, scaling with player count. Exceeding it
**queues** requests rather than failing them, which presents as the game hanging:

`DataStore request was added to queue.`

```lua
local budget = DataStoreService:GetRequestBudgetForRequestType(
	Enum.DataStoreRequestType.SetIncrementAsync
)
```

The rules that keep you under it: one save per player per cycle carrying one table,
autosave no faster than about 60 seconds, cached reads instead of repeated
`GetAsync`, and exponential backoff on retries.

## What can be stored

Numbers, strings, booleans, and tables of those. **Not** instances, `Vector3`,
`CFrame`, `Color3`, or functions — serialise them first:

```lua
data.Spawn = { pos.X, pos.Y, pos.Z }
local pos = Vector3.new(unpack(data.Spawn))
```

Tables with mixed or non-string keys serialise unreliably. Keep keys as strings, or
use a clean array.

## Version the store name

`PlayerData_v1` rather than `PlayerData`. When your format eventually changes in a way
old saves cannot handle, bumping the version is far easier than writing a migration.
Decide this on day one — changing the name later abandons everyone's progress.

## Shutdown

`Players.PlayerRemoving` does not reliably fire for everyone when a server shuts down.
`game:BindToClose` gives you a short window (around 30 seconds) to finish:

```lua
game:BindToClose(function()
	for _, player in ipairs(Players:GetPlayers()) do
		task.spawn(saveData, player)
	end
	task.wait(3)
end)
```

`BindToClose` does **not** run when you stop a Studio playtest, so it can only be
verified in a live server.

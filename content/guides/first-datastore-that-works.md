---
title: "Your first DataStore that doesn't lose player data"
description: A save system that handles failures, retries, and server shutdown — the three things a naive DataStore script gets wrong.
date: 2026-08-06
category: Data
kind: learn
level: Intermediate
minutes: 13
---

Most first DataStore scripts look like this:

```lua
local DataStoreService = game:GetService("DataStoreService")
local store = DataStoreService:GetDataStore("PlayerData")

game.Players.PlayerAdded:Connect(function(player)
	local data = store:GetAsync(player.UserId)
	player.Coins.Value = data or 0
end)

game.Players.PlayerRemoving:Connect(function(player)
	store:SetAsync(player.UserId, player.Coins.Value)
end)
```

It works when you test it. It loses data in production, for three specific reasons:

1. `GetAsync` can fail. If it does, this errors, and `Coins` never gets set — and
   then the save on exit writes the default over their real data.
2. `PlayerRemoving` does not fire for everyone when a server shuts down.
3. Nothing retries, so one network blip is permanent data loss.

Here is a version that handles all three.

## Turn the API access on first

DataStores do not work in Studio until you allow it:

**Home → Game Settings → Security → Enable Studio Access to API Services.**

Without this, every call fails with a message about API services, and you will
spend an hour debugging code that is fine.

Also note that DataStores do not work at all in an unpublished place. Publish once
before testing.

## Wrap every call

Every DataStore call goes over the network and can fail. `pcall` is not optional
here:

```lua
local DataStoreService = game:GetService("DataStoreService")
local store = DataStoreService:GetDataStore("PlayerData_v1")

local function safeCall(fn, ...)
	local attempts = 0
	while attempts < 3 do
		attempts += 1
		local ok, result = pcall(fn, ...)
		if ok then
			return true, result
		end
		warn("[Data] attempt", attempts, "failed:", result)
		task.wait(2 ^ attempts)   -- 2s, 4s, 8s
	end
	return false, nil
end
```

The doubling wait is deliberate. Retrying immediately usually fails again for the
same reason; backing off gives a transient problem time to clear.

> [!note]
> Note the `_v1` in the store name. When you eventually change your data format in
> a way old saves cannot handle, bumping to `_v2` is far easier than writing a
> migration. Decide this on day one — renaming later abandons everyone's progress.

## Load, with a default and a failure flag

```lua
local DEFAULT_DATA = {
	Coins = 0,
	Level = 1,
	Inventory = {},
}

local cache = {}         -- [userId] = data table
local dataFailed = {}    -- [userId] = true if the load failed

local function copyDefaults()
	return {
		Coins = DEFAULT_DATA.Coins,
		Level = DEFAULT_DATA.Level,
		Inventory = {},
	}
end

local function loadData(player)
	local ok, result = safeCall(function()
		return store:GetAsync(player.UserId)
	end)

	if not ok then
		-- Could not reach the DataStore. Give them a working session but
		-- REFUSE to save, or we would overwrite real data with defaults.
		dataFailed[player.UserId] = true
		cache[player.UserId] = copyDefaults()
		warn("[Data] load failed for", player.Name, "- saving disabled")
		return
	end

	local data = result or copyDefaults()

	-- fill in any key added since this save was written
	for key, value in pairs(DEFAULT_DATA) do
		if data[key] == nil then
			data[key] = typeof(value) == "table" and {} or value
		end
	end

	cache[player.UserId] = data
end
```

That `dataFailed` flag is the most important part of this whole guide. **A failed
load must disable saving for that session.** Otherwise the sequence is: load fails
→ player gets defaults → player leaves → defaults get saved → their real progress
is gone forever. This single check prevents the worst class of data loss.

## Save, refusing when the load failed

```lua
local function saveData(player)
	local userId = player.UserId
	local data = cache[userId]

	if not data then
		return
	end
	if dataFailed[userId] then
		warn("[Data] not saving", player.Name, "- load had failed")
		return
	end

	local ok = safeCall(function()
		return store:SetAsync(userId, data)
	end)

	if not ok then
		warn("[Data] SAVE FAILED for", player.Name)
	end
end
```

## Handle server shutdown

`PlayerRemoving` fires when one player leaves. When the whole server shuts down —
which happens constantly, on updates and when a server empties — it may not fire
for everyone before the process ends.

`game:BindToClose` is the hook for that. Roblox gives the server a short window
(around 30 seconds) to finish up:

```lua
local Players = game:GetService("Players")

Players.PlayerAdded:Connect(loadData)
Players.PlayerRemoving:Connect(function(player)
	saveData(player)
	cache[player.UserId] = nil
	dataFailed[player.UserId] = nil
end)

game:BindToClose(function()
	for _, player in ipairs(Players:GetPlayers()) do
		task.spawn(saveData, player)
	end
	task.wait(3)   -- give the spawned saves a moment to land
end)
```

`task.spawn` matters here: saving twenty players one after another at two seconds
each would exceed the shutdown window. Firing them in parallel fits.

> [!warning]
> `BindToClose` does **not** run in Studio when you stop a playtest with the stop
> button, so you cannot verify it there. Test it in a real server by joining,
> earning something, and closing the client — then rejoin and check.

## Autosave

Even with both hooks, a server crash loses everything since the last save. Autosave
puts a floor on how much:

```lua
task.spawn(function()
	while task.wait(120) do
		for _, player in ipairs(Players:GetPlayers()) do
			saveData(player)
		end
	end
end)
```

Two minutes is a reasonable starting point. Do not go much below 60 seconds — you
will run into request limits.

## The limits you will hit

Roblox caps how many DataStore requests a server may make. The budget scales with
player count, and exceeding it queues your requests rather than failing them, which
looks like the game hanging.

```lua
local budget = DataStoreService:GetRequestBudgetForRequestType(
	Enum.DataStoreRequestType.SetIncrementAsync
)
print("remaining save budget:", budget)
```

The practical rules that keep you inside it:

- One save per player per autosave cycle, not one per stat.
- Save the whole table in a single `SetAsync`, never a call per field.
- Never call a DataStore inside a loop that runs per frame or on `Touched`.

## What to store

Store plain data: numbers, strings, booleans, and tables of those.

You cannot store instances, `Vector3`, `CFrame`, `Color3`, or functions. Convert
them:

```lua
-- instead of storing a CFrame
data.SpawnPosition = { pos.X, pos.Y, pos.Z }

-- reading it back
local pos = Vector3.new(unpack(data.SpawnPosition))
```

Tables with non-string, non-sequential keys also serialise badly. If a save comes
back with keys missing, that is usually why — keep keys as strings or a clean
array.

<!-- OWN_EXPERIENCE -->

## Verifying it actually works

1. Enable Studio API access and publish the place.
2. Join the live game, change a value, leave, rejoin. The value should persist.
3. Rename the store to something that has never existed and rejoin — you should get
   defaults, with no errors.
4. Check the server log (`F9` → Server) for any `[Data]` warnings. Those lines are
   there so that a failure is visible instead of silent.

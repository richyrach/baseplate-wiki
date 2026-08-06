---
title: "'DataStore request was added to queue': what throttling actually means"
description: This warning means you are over your request budget. Here is how the budget works and how to get back under it.
date: 2026-08-06
category: Data
kind: learn
level: Intermediate
minutes: 9
---

The message reads roughly:

`DataStore request was added to queue. If request queue fills, further requests will be dropped.`

It is a warning, not an error, and the important word is **queue**. Your request
was not rejected. It was parked, and it will run later — possibly seconds later.
That delay is why the symptom people describe is "my game freezes when someone
joins" rather than "saving failed."

If the queue fills, requests do start getting dropped. That is when data loss
begins.

## The budget

Every server gets an allowance of DataStore requests per minute, and it scales with
the number of players. Roughly: a base amount plus an amount per player.

You can read what is left:

```lua
local DataStoreService = game:GetService("DataStoreService")

local budget = DataStoreService:GetRequestBudgetForRequestType(
	Enum.DataStoreRequestType.SetIncrementAsync
)
print("save budget remaining:", budget)
```

The request types are counted separately:

| Type | Covers |
|---|---|
| `GetAsync` | reads |
| `SetIncrementAsync` | `SetAsync`, `IncrementAsync` |
| `UpdateAsync` | `UpdateAsync` |
| `GetSortedAsync` | ordered data store reads |
| `SetIncrementSortedAsync` | ordered data store writes |

So a game that reads a lot and writes rarely can exhaust its read budget while its
write budget sits untouched.

## The four things that actually cause it

**Saving per stat instead of per player.** This is the big one:

```lua
-- four requests per player
store:SetAsync(userId .. "_coins", coins)
store:SetAsync(userId .. "_level", level)
store:SetAsync(userId .. "_xp", xp)
store:SetAsync(userId .. "_items", items)
```

One table, one request:

```lua
store:SetAsync(userId, {
	Coins = coins,
	Level = level,
	XP = xp,
	Items = items,
})
```

Twenty players just went from 80 requests to 20.

**Saving on every change.** A coin pickup that saves immediately means a player
running through a coin room generates dozens of writes in seconds.

Mark the data dirty instead, and let the autosave loop write it:

```lua
local dirty = {}

local function addCoins(player, amount)
	local data = cache[player.UserId]
	if not data then return end

	data.Coins += amount
	dirty[player.UserId] = true     -- no DataStore call here
end

task.spawn(function()
	while task.wait(60) do
		for userId in pairs(dirty) do
			local player = Players:GetPlayerByUserId(userId)
			if player then
				saveData(player)
			end
			dirty[userId] = nil
		end
	end
end)
```

The in-memory value is what gameplay reads, so the player sees their coins update
instantly. The DataStore is just durable storage, and it does not need to be
current to the millisecond.

**Retry loops with no backoff.** A failing call retried every frame burns the whole
budget in seconds and guarantees continued failure:

```lua
-- wrong
while not success do
	success = pcall(save)
end

-- right
for attempt = 1, 3 do
	if pcall(save) then break end
	task.wait(2 ^ attempt)
end
```

**Reading in a loop.** `GetAsync` inside anything that repeats — a `Touched`
handler, a leaderboard refresh, a shop opening — should be a cached read instead.
Load once on join, keep it in memory.

## Checking the budget before you spend it

For non-urgent writes, wait for budget rather than queueing:

```lua
local function waitForBudget(requestType)
	local start = os.clock()
	while DataStoreService:GetRequestBudgetForRequestType(requestType) < 1 do
		if os.clock() - start > 30 then
			return false      -- give up rather than block forever
		end
		task.wait(1)
	end
	return true
end

if waitForBudget(Enum.DataStoreRequestType.SetIncrementAsync) then
	safeCall(function() return store:SetAsync(userId, data) end)
end
```

Do **not** do this inside `BindToClose`. There you have a few seconds total and
should just fire the saves.

## SetAsync vs UpdateAsync

`UpdateAsync` reads and writes in one operation, which makes it the correct choice
when the new value depends on the old one — currency, counters, anything two servers
might touch:

```lua
store:UpdateAsync(userId, function(old)
	local data = old or { Coins = 0 }
	data.Coins += 50
	return data
end)
```

With `SetAsync`, two servers can both read 100, both add 50, and both write 150 —
one increment vanishes. `UpdateAsync` cannot lose that way.

It costs one request from a different budget, so it is not a free win, but for
anything incremental it is the right tool.

> [!warning]
> The function you pass to `UpdateAsync` must not yield. No `task.wait`, no
> DataStore calls, no `WaitForChild` inside it. Compute and return.

## Reading the diagnosis

The warning tells you the request type. Match it to the table above and you know
which side is over budget — reads or writes. Then:

- **Writes over budget** → you are saving too often, or per-stat instead of per-
  player.
- **Reads over budget** → you are reading in a loop instead of caching on join.

Add a budget print to your autosave loop and watch it for a few minutes on a busy
server. If it trends toward zero, the fix is fewer calls, not longer retries.

## The short checklist

1. One `SetAsync` per player per save, carrying one table.
2. Autosave on a timer, 60 seconds or slower. Never save on every change.
3. Every retry backs off. No tight retry loops.
4. `GetAsync` once on join, cached in memory after that.
5. `UpdateAsync` for anything incremental.

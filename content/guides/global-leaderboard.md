---
title: "A global leaderboard with OrderedDataStore"
description: A top-ten board that persists across servers, updates without hammering the request budget, and does not break when a name fails to load.
date: 2026-08-06
category: Data
kind: recipe
level: Advanced
minutes: 12
---

The player list shows stats for people in your server. A **global** leaderboard ranks
everyone who has ever played, which needs an `OrderedDataStore` — a data store that
can return its keys sorted by value.

## The two stores

An `OrderedDataStore` can only hold **integers**. That is the trade for being
sortable. Keep your real player data in a normal `DataStore` and mirror just the one
ranked number into the ordered one.

```lua
local DataStoreService = game:GetService("DataStoreService")

local playerData = DataStoreService:GetDataStore("PlayerData_v1")
local coinBoard = DataStoreService:GetOrderedDataStore("CoinLeaderboard_v1")
```

Version the name. If you ever need to reset the board — a new season, a fixed
exploit — you bump to `_v2` rather than trying to delete thousands of keys.

## Writing a score

```lua
local function publishScore(player, coins)
	local value = math.floor(coins)
	if value < 0 or value ~= value then     -- negative or NaN
		return
	end

	local ok, err = pcall(function()
		coinBoard:SetAsync(tostring(player.UserId), value)
	end)

	if not ok then
		warn("[Board] publish failed for", player.Name, err)
	end
end
```

The key must be a **string**, so `tostring(player.UserId)`. Passing the number works
in some places and not others; be consistent.

`math.floor` is not optional — an `OrderedDataStore` rejects non-integers, and a
fractional coin count from a multiplier will fail the whole write.

Publish on the same schedule as your autosave, not on every change. A player earning
coins in a loop would otherwise generate a write per coin and exhaust the budget.

## Reading the top ten

```lua
local function fetchTop(count)
	local ok, pages = pcall(function()
		-- descending, values between 0 and a very large number
		return coinBoard:GetSortedAsync(false, count, 0, 10 ^ 12)
	end)

	if not ok then
		warn("[Board] fetch failed:", pages)
		return nil
	end

	local page = pages:GetCurrentPage()
	local results = {}

	for rank, entry in ipairs(page) do
		results[rank] = {
			userId = tonumber(entry.key),
			score = entry.value,
		}
	end

	return results
end
```

`GetSortedAsync(ascending, pageSize, minValue, maxValue)`:

- `false` for descending, which is what a "top" board wants.
- `pageSize` is how many per page — keep it to what you display.
- The min and max bound which values are considered. Passing a wide range is fine;
  passing `nil` for both is also allowed but being explicit avoids surprises with
  negative values.

Each entry has `.key` (your string key) and `.value` (the integer).

## Turning user IDs into names

The board stores IDs. Displaying "1234567" is useless, and this is where most
leaderboard code falls over — `GetNameFromUserIdAsync` is a web call that can fail or
be slow, and doing ten of them serially on every refresh is a visible stall.

```lua
local Players = game:GetService("Players")

local nameCache = {}

local function nameFor(userId)
	if nameCache[userId] then
		return nameCache[userId]
	end

	local ok, name = pcall(function()
		return Players:GetNameFromUserIdAsync(userId)
	end)

	if ok and name then
		nameCache[userId] = name
		return name
	end

	return "Player " .. userId       -- degrade, do not error
end
```

Cache aggressively — names change rarely and a wrong name for an hour is far better
than a broken board. Always have a fallback string, because one failed lookup must not
take out the other nine rows.

## Putting it together

```lua
local REFRESH_SECONDS = 60

local boardValue = Instance.new("StringValue")
boardValue.Name = "LeaderboardJson"
boardValue.Parent = game:GetService("ReplicatedStorage")

local HttpService = game:GetService("HttpService")

local function refresh()
	local top = fetchTop(10)
	if not top then
		return          -- keep showing the previous board
	end

	for _, row in ipairs(top) do
		row.name = nameFor(row.userId)
	end

	boardValue.Value = HttpService:JSONEncode(top)
end

task.spawn(function()
	while true do
		refresh()
		task.wait(REFRESH_SECONDS)
	end
end)
```

Publishing one JSON string into `ReplicatedStorage` means every client — including
players who join later — can read the current board without a RemoteEvent per client.
`JSONEncode` needs no HTTP permission; `HttpService` is only being used for its
encoder.

Returning early on failure is deliberate: a stale board beats a blank one.

## The client side

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")

local boardValue = ReplicatedStorage:WaitForChild("LeaderboardJson")
local container = script.Parent:WaitForChild("Rows")
local template = script.Parent:WaitForChild("RowTemplate")

local function redraw()
	if boardValue.Value == "" then
		return
	end

	local ok, rows = pcall(function()
		return HttpService:JSONDecode(boardValue.Value)
	end)
	if not ok then
		return
	end

	for _, child in ipairs(container:GetChildren()) do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end

	for rank, row in ipairs(rows) do
		local item = template:Clone()
		item.LayoutOrder = rank
		item.RankLabel.Text = "#" .. rank
		item.NameLabel.Text = row.name
		item.ScoreLabel.Text = string.format("%d", row.score)
		item.Visible = true
		item.Parent = container
	end
end

boardValue.Changed:Connect(redraw)
redraw()
```

## Budget

`GetSortedAsync` draws from its own budget, separate from ordinary reads:

```lua
local budget = DataStoreService:GetRequestBudgetForRequestType(
	Enum.DataStoreRequestType.GetSortedAsync
)
```

One refresh per minute per server is comfortable. One per player action is not — and
because every server refreshes independently, a popular game with fifty servers is
making fifty times as many calls as you are thinking about.

> [!warning]
> An `OrderedDataStore` is trivially poisoned by an exploit. If a player can grant
> themselves currency, they land at rank one permanently and your board becomes a
> billboard for the bug. Publish scores from server-authoritative values only — see
> the guide on a currency the client cannot edit.

## Resetting for a new season

Do not iterate and delete. Bump the store name:

```lua
local coinBoard = DataStoreService:GetOrderedDataStore("CoinLeaderboard_v2")
```

The old data stays untouched, so you can still read last season's board if you want an
archive.

## Testing it

1. Enable Studio API access and publish the place.
2. Write a few fake entries from the Command Bar with different values, then check that
   `fetchTop` returns them in descending order.
3. Set one value to a non-integer and confirm you see the write fail — that is the
   `math.floor` lesson, and it is better to see it once deliberately.
4. Break `nameFor` on purpose (return `nil`) and confirm the board still renders with
   the fallback text rather than erroring.

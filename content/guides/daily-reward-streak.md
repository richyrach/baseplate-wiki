---
title: "A daily reward streak that cannot be cheated by changing the clock"
description: Tracking daily logins with server time, handling broken streaks, and why os.time on the client is worthless for this.
date: 2026-08-06
category: Data
kind: recipe
level: Intermediate
minutes: 11
---

A daily reward looks simple and has one hard part: deciding what "a new day" means, in
a way a player cannot manipulate.

## Use server time, always

```lua
-- WRONG: this is the player's own clock
local now = os.time()          -- in a LocalScript
```

A client's `os.time()` is the time on their machine. They can change it. Any streak
logic built on a client timestamp can be advanced by setting the system clock forward.

On the **server**, `os.time()` is the server's clock, which players do not control.
That is what you want.

```lua
-- ServerScriptService
local now = os.time()          -- seconds since epoch, UTC, server-side
```

`workspace:GetServerTimeNow()` is also server-authoritative but measures elapsed time
rather than wall-clock date, so it is the wrong tool for "which calendar day is it."

## Deciding what a day is

Two approaches, and the difference matters more than it looks.

**Calendar day (UTC).** A new day starts at UTC midnight.

```lua
local function dayNumber(unixTime)
	return math.floor(unixTime / 86400)
end
```

Simple, and everyone's streak resets at the same moment. The downside: a player in
Iran claiming at 3am local time is on a different UTC day than they expect, and can
feel like they lost a streak unfairly.

**Rolling 24 hours.** A new claim is available 24 hours after the last one.

```lua
local COOLDOWN = 24 * 60 * 60
local canClaim = (now - lastClaim) >= COOLDOWN
```

Fair across time zones, but it drifts — claim at 8pm, then 8:05pm the next day, and by
the end of the week you are claiming at midnight.

**The compromise most games use**, and what I would recommend: calendar days for the
streak, with a grace window so a late claim does not break it.

```lua
local GRACE_DAYS = 1        -- miss one day and the streak survives

local function evaluate(lastClaimDay, today)
	if lastClaimDay == nil then
		return "first"
	elseif today == lastClaimDay then
		return "already"
	elseif today - lastClaimDay <= 1 + GRACE_DAYS then
		return "continue"
	else
		return "broken"
	end
end
```

## The reward table

```lua
local REWARDS = {
	[1] = { coins = 50 },
	[2] = { coins = 75 },
	[3] = { coins = 100 },
	[4] = { coins = 150 },
	[5] = { coins = 200 },
	[6] = { coins = 300 },
	[7] = { coins = 500, item = "WeeklyCrate" },
}

local function rewardFor(streak)
	-- cycles every 7 days, so day 8 is day 1's reward again
	local index = ((streak - 1) % #REWARDS) + 1
	return REWARDS[index]
end
```

Cycling rather than growing forever keeps the numbers sane. A linear reward that
increases every day becomes absurd by day 200.

## The claim, server-side

```lua
-- ServerScriptService/DailyReward.server.lua
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local claimRemote = ReplicatedStorage.Remotes:WaitForChild("ClaimDaily")

local function dayNumber(unixTime)
	return math.floor(unixTime / 86400)
end

local function tryClaim(player)
	local data = cache[player.UserId]        -- your loaded save table
	if not data then
		return false, "Data not loaded"
	end

	local today = dayNumber(os.time())
	local outcome = evaluate(data.lastClaimDay, today)

	if outcome == "already" then
		return false, "Come back tomorrow"
	end

	if outcome == "first" then
		data.streak = 1
	elseif outcome == "continue" then
		data.streak = (data.streak or 0) + 1
	else
		data.streak = 1                       -- broken, start again
	end

	data.lastClaimDay = today

	local reward = rewardFor(data.streak)
	addBalance(player, reward.coins)
	if reward.item then
		grantItem(player, reward.item)
	end

	markDirty(player)                         -- let the autosave write it

	return true, reward, data.streak
end

claimRemote.OnServerInvoke = function(player)
	if rateLimited(player) then
		return false, "Too fast"
	end
	return tryClaim(player)
end
```

## The five things that make it safe

**The remote takes no arguments.** The client says "I want to claim." It does not say
which day it is, how long its streak is, or what reward it should get. Every one of
those is computed server-side. This single design choice removes most of the attack
surface.

**`lastClaimDay` is stored, not `lastClaimTime`.** Storing a day number rather than a
timestamp means the "already claimed" check is an integer comparison and cannot be
defeated by a few seconds of clock skew.

**The rate limit is on the handler.** `OnServerInvoke` can be called repeatedly; without
a limit, a player can fire ten claims in one frame and — if your data write is slow —
have several pass the `already` check before the first one lands.

**The write happens before the reward is reported.** `data.lastClaimDay = today` is set
before granting, so even if granting fails the day is consumed. That is the safe
direction for an exploit: worst case a player loses one reward, rather than farming
infinite ones.

**Nothing trusts `data.streak` from the client.** It lives in the server's cache and is
saved with the rest of the player's data.

> [!warning]
> If your DataStore save is asynchronous — and it should be — a player who claims and
> immediately leaves may not have the write persisted. Save on claim as well as on the
> autosave timer for anything this visible, or players will report losing streaks.

## Showing the state to the client

```lua
local function claimState(player)
	local data = cache[player.UserId]
	if not data then
		return { ready = false }
	end

	local today = dayNumber(os.time())
	local outcome = evaluate(data.lastClaimDay, today)

	return {
		ready = outcome ~= "already",
		streak = data.streak or 0,
		nextReward = rewardFor((data.streak or 0) + 1),
		secondsUntilTomorrow = ((today + 1) * 86400) - os.time(),
	}
end
```

Sending `secondsUntilTomorrow` lets the client run its own countdown without asking the
server again. The client displays it; the server still decides whether a claim is
allowed, so a client with a manipulated countdown just sees a wrong number and gets
refused.

## Client side

```lua
local claimRemote = ReplicatedStorage.Remotes:WaitForChild("ClaimDaily")

button.Activated:Connect(function()
	button.Active = false

	local ok, result, streak = pcall(function()
		return claimRemote:InvokeServer()
	end)

	if not ok then
		statusLabel.Text = "Something went wrong"
	elseif result == false then
		statusLabel.Text = tostring(streak)     -- the message
	else
		statusLabel.Text = string.format("Day %d! +%d coins", streak, result.coins)
	end

	task.wait(1)
	button.Active = true
end)
```

Note the `pcall` around `InvokeServer`. A `RemoteFunction` that errors on the server
throws on the client, and without the `pcall` the button stays disabled forever.

## Testing it without waiting a day

Temporarily override the day function in Studio:

```lua
local FAKE_DAY_OFFSET = 0        -- bump this to simulate days passing

local function dayNumber(unixTime)
	return math.floor(unixTime / 86400) + FAKE_DAY_OFFSET
end
```

Then in the Command Bar, change `FAKE_DAY_OFFSET` and claim again. Walk through all
four outcomes:

1. First ever claim → streak 1.
2. Claim again immediately → refused.
3. Offset +1, claim → streak 2.
4. Offset +5, claim → streak resets to 1.

Delete the offset before publishing. Shipping it is shipping a free reward button.

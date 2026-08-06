---
title: "Awarding badges without spamming the API"
description: AwardBadgeAsync, checking first so you do not re-award, and why this must be server-side and wrapped in pcall.
date: 2026-08-06
category: Data
kind: recipe
level: Intermediate
minutes: 8
---

Badges are achievements that live on the player's Roblox profile rather than in your
data store, which makes them permanent and visible outside your game. That is the
appeal, and it is also why the API is stricter than most.

## The current methods

```lua
local BadgeService = game:GetService("BadgeService")

BadgeService:AwardBadgeAsync(userId, badgeId)      -- yields, returns boolean
BadgeService:UserHasBadgeAsync(userId, badgeId)    -- yields, returns boolean
BadgeService:GetBadgeInfoAsync(badgeId)            -- yields, returns a table
```

> [!warning]
> `BadgeService:AwardBadge()` — without `Async` — is **deprecated**. Almost every
> tutorial and forum post still shows the old name. Use `AwardBadgeAsync`.

## The working pattern

```lua
-- ServerScriptService/Badges.server.lua
local BadgeService = game:GetService("BadgeService")
local Players = game:GetService("Players")

local BADGES = {
	FirstJoin = 1111111111,
	ReachedLevel10 = 2222222222,
}

-- [userId] = { [badgeId] = true }
local awarded = {}

local function hasBadge(userId, badgeId)
	local cached = awarded[userId]
	if cached and cached[badgeId] then
		return true
	end

	local ok, result = pcall(function()
		return BadgeService:UserHasBadgeAsync(userId, badgeId)
	end)

	if not ok then
		warn("[Badge] ownership check failed:", result)
		return nil                      -- unknown, not "no"
	end

	if result then
		awarded[userId] = awarded[userId] or {}
		awarded[userId][badgeId] = true
	end

	return result
end

local function award(player, badgeId)
	local userId = player.UserId

	local owns = hasBadge(userId, badgeId)
	if owns ~= false then
		-- true (already has it) or nil (we don't know) -- either way, don't award
		return false
	end

	local ok, granted = pcall(function()
		return BadgeService:AwardBadgeAsync(userId, badgeId)
	end)

	if not ok then
		warn("[Badge] award failed:", granted)
		return false
	end

	if granted then
		awarded[userId] = awarded[userId] or {}
		awarded[userId][badgeId] = true
	end

	return granted
end

Players.PlayerRemoving:Connect(function(player)
	awarded[player.UserId] = nil
end)
```

## Why check before awarding

`AwardBadgeAsync` on a badge the player already owns is a wasted web request, and
badge endpoints are rate-limited. Awarding in a loop — say from a `Touched` event —
will get you throttled, and then the players who genuinely earned it do not receive it.

Checking first, and caching the result, turns a repeated award attempt into a table
lookup.

## Why `owns ~= false` and not `not owns`

`hasBadge` returns three values: `true`, `false`, and `nil` for "the check failed."

`not owns` would treat `nil` as "does not own" and attempt an award on an unknown
state — exactly the case where you are most likely to be hitting an API problem
already. `owns ~= false` only proceeds when we positively know they do not have it.

## It must be server-side

`AwardBadgeAsync` only works from a server script. Calling it from a LocalScript fails.

That is the correct design: badges are permanent profile changes, and a client should
never be able to decide it has earned one. The client can *ask* — "I finished the
level" — and the server verifies and awards, the same pattern as currency.

## The badge must belong to this game

A badge can only be awarded by the experience it was created under. Badges from
another game, or ones you created under a different place, silently fail to award.

If awarding returns `false` with no error, this is the first thing to check.

## Showing badge info in your UI

```lua
local function badgeDetails(badgeId)
	local ok, info = pcall(function()
		return BadgeService:GetBadgeInfoAsync(badgeId)
	end)

	if not ok then
		return nil
	end

	return {
		name = info.Name,
		description = info.Description,
		icon = "rbxassetid://" .. info.IconImageId,
		enabled = info.IsEnabled,
	}
end
```

`IsEnabled` is worth reading — a disabled badge cannot be awarded, and this is a
common cause of "my award call returns false" after someone toggles it in the
dashboard.

Cache this too. Badge metadata almost never changes.

## Awarding on a real achievement

```lua
local function onLevelUp(player, newLevel)
	if newLevel >= 10 then
		task.spawn(award, player, BADGES.ReachedLevel10)
	end
end
```

`task.spawn` matters. `AwardBadgeAsync` yields, and you do not want a badge award —
which involves two web requests — blocking the level-up code that the player is
actually waiting on.

For a first-join badge, award after a short delay rather than instantly on
`PlayerAdded`:

```lua
Players.PlayerAdded:Connect(function(player)
	task.spawn(function()
		task.wait(5)
		if player.Parent then         -- still in the server
			award(player, BADGES.FirstJoin)
		end
	end)
end)
```

The `player.Parent` check stops you making a web request for someone who joined and
immediately left, which on a popular game is a meaningful share of joins.

## When an award silently fails

In order of likelihood:

1. The badge belongs to a different experience.
2. The badge is disabled in the Creator Dashboard.
3. You are calling it from a LocalScript.
4. The player already owns it — which is a success, not a failure.
5. You are being rate-limited, usually because the award is inside a loop or an
   event that fires repeatedly.
6. You are still using the deprecated `AwardBadge` instead of `AwardBadgeAsync`.

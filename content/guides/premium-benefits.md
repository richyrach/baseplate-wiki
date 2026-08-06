---
title: "Giving Premium players benefits, and the Roblox Plus problem"
description: How to detect Premium in 2026 — including why the usual MembershipType check now also returns true for Roblox Plus subscribers.
date: 2026-08-06
category: Monetization
kind: learn
level: Intermediate
minutes: 11
---

Premium benefits are a good deal for developers: you get paid through
engagement-based payouts for time Premium players spend in your game, so giving them
a visible perk is directly worth doing.

The detection, however, is currently messier than every tutorial online says.

## The check everyone shows you

```lua
if player.MembershipType == Enum.MembershipType.Premium then
	grantPremiumPerks(player)
end
```

This is the pattern in essentially every guide and video. There are two problems with
it as of 2026.

## Problem 1: MembershipType is deprecated

`Player.MembershipType` is marked deprecated in the current API reference. Deprecated
properties keep working for a long time, so this is not urgent — but it does mean any
code built on it has a shelf life.

## Problem 2: it now returns Premium for Roblox Plus subscribers

Roblox introduced **Roblox Plus** on 30 April 2026 as a separate subscription from
Premium. `Player.MembershipType` returns `Enum.MembershipType.Premium` for Plus
subscribers as well as Premium ones.

This was raised as a bug, and Roblox staff confirmed it is **intentional, for
backwards compatibility**, recommending `HasRobloxSubscription` instead for
distinguishing the two.

The practical consequence: if you use the standard check, Roblox Plus subscribers get
your Premium perks. Whether that matters depends on your game. If the perk is
cosmetic, it is probably fine. If it is a currency multiplier tied to payouts you only
receive for actual Premium members, you are giving away value you are not being paid
for.

> [!warning]
> `Player.HasRobloxSubscription` is a boolean, but the API reference lists its
> security level as **Roblox Security** — which normally means scripts in your game
> cannot read it. I have not been able to confirm whether developer scripts can
> actually access it in a live game. Before building anything on it, test it in your
> own published place and see whether reading it errors. Do not take my word, or a
> forum post's, for this one.

That caveat is the honest state of it. The situation is in flux, and I would rather
say so than hand you a confident snippet that throws.

## What to do in the meantime

Use `MembershipType`, and know what it includes:

```lua
-- ServerScriptService/PremiumPerks.server.lua
local Players = game:GetService("Players")

local COIN_MULTIPLIER = 2

local isPremium = {}      -- [userId] = boolean

local function hasSubscription(player)
	-- NOTE: as of Aug 2026 this is true for both Premium and Roblox Plus.
	return player.MembershipType == Enum.MembershipType.Premium
end

local function applyPerks(player)
	if not isPremium[player.UserId] then
		return
	end

	player:SetAttribute("CoinMultiplier", COIN_MULTIPLIER)

	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if humanoid then
		humanoid.WalkSpeed = 20
	end
end

Players.PlayerAdded:Connect(function(player)
	isPremium[player.UserId] = hasSubscription(player)
	applyPerks(player)

	player.CharacterAdded:Connect(function()
		task.wait(0.1)
		applyPerks(player)
	end)
end)

Players.PlayerRemoving:Connect(function(player)
	isPremium[player.UserId] = nil
end)
```

Using an **attribute** for the multiplier rather than a `Value` object is convenient:
attributes replicate to clients automatically, so your UI can read
`player:GetAttribute("CoinMultiplier")` and show a badge, while the server remains the
only thing that writes it.

Re-apply on `CharacterAdded`, because `WalkSpeed` lives on the `Humanoid` and the
character is rebuilt on every respawn.

## Reacting to a mid-session purchase

```lua
Players.PlayerMembershipChanged:Connect(function(player)
	isPremium[player.UserId] = hasSubscription(player)
	applyPerks(player)
end)
```

This event has a significant limitation worth knowing: in practice it fires when the
player's membership changes **during the session after being prompted**, not as a
general-purpose subscription watcher. Do not rely on it to catch every possible
change. The join-time check is what carries the weight.

## Prompting for Premium

`MarketplaceService:PromptPremiumPurchase(player)` is **deprecated**.

I do not have a verified current replacement to give you. If you want to advertise
Premium, the reliable approach today is a normal in-game UI panel explaining the
benefit, rather than an engine-provided prompt — and check the current
MarketplaceService reference before building around any prompt method, because this
area of the API has changed more than once.

## Do not gate core gameplay behind it

Worth saying because it is a design mistake more than a coding one: perks that make
the game *unplayable* without Premium read badly and lose you non-Premium players,
who are the overwhelming majority.

Things that work well:

- a currency or XP multiplier
- a cosmetic — a trail, a name colour, a chat tag
- an extra inventory slot or save slot
- access to a lounge area

Things that go badly: extra damage in a competitive mode, meaningfully faster
progression in a leaderboard game, or anything that makes free players feel like the
game is worse on purpose.

## Client-side display

```lua
-- LocalScript
local player = game:GetService("Players").LocalPlayer

local function refreshBadge()
	local multiplier = player:GetAttribute("CoinMultiplier") or 1
	badge.Visible = multiplier > 1
	badge.Text = string.format("%dx coins", multiplier)
end

player:GetAttributeChangedSignal("CoinMultiplier"):Connect(refreshBadge)
refreshBadge()
```

The client reads and displays; the server decides and writes. Same rule as every other
system — see the guide on a currency the client cannot edit.

## Where this stands

1. `MembershipType` works, is deprecated, and currently includes Roblox Plus.
2. `HasRobloxSubscription` is the recommended replacement but is documented as
   Roblox-security restricted — **test whether you can read it before relying on it.**
3. `PromptPremiumPurchase` is deprecated with no replacement I can confirm.
4. Check membership on join, cache it, re-apply perks on respawn.
5. Keep perks additive, never gate core gameplay.

If you test the `HasRobloxSubscription` access question and find a definitive answer,
that is exactly the kind of correction this site wants —
[send it in](../contribute.html).

## Sources

- [Player.MembershipType — Roblox API reference](https://create.roblox.com/docs/reference/engine/classes/Player)
- [MembershipType returns Premium for Roblox Plus subscribers — Roblox DevForum](https://devforum.roblox.com/t/playermembershiptype-returns-premium-for-roblox-plus-subscribers/4607269)
- [Engagement-based payouts — Roblox documentation](https://create.roblox.com/docs/production/monetization/engagement-based-payouts)

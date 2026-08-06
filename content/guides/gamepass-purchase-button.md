---
title: "A game pass button that checks ownership before prompting"
description: Prompting a game pass purchase from a GUI button, checking whether they already own it, and granting the benefit on the server where it counts.
date: 2026-08-06
category: Monetization
kind: recipe
level: Beginner
minutes: 10
---

A button that sells a game pass has three jobs: don't try to sell it to someone who
already owns it, prompt correctly, and grant the benefit **on the server** once the
purchase goes through.

Most tutorials get the first and third wrong.

## Getting the pass ID

The ID is in the URL of the game pass page on the Roblox website — the number in
`.../game-pass/123456789/Name`. It is **not** the same as the asset ID shown in
Studio's toolbox, and passing the wrong one produces a prompt that fails silently.

## The client button

```lua
-- StarterPlayerScripts, or a LocalScript inside the button
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")

local PASS_ID = 123456789          -- your game pass ID

local player = Players.LocalPlayer
local button = script.Parent

local function ownsPass()
	local ok, owns = pcall(function()
		return MarketplaceService:UserOwnsGamePassAsync(player.UserId, PASS_ID)
	end)

	if not ok then
		warn("[Pass] ownership check failed:", owns)
		return nil                  -- nil means "we don't know"
	end
	return owns
end

button.Activated:Connect(function()
	button.Active = false

	local owns = ownsPass()
	if owns == true then
		button.Text = "Already owned"
	elseif owns == nil then
		button.Text = "Try again"    -- the check failed, not "they don't own it"
	else
		MarketplaceService:PromptGamePassPurchase(player, PASS_ID)
	end

	task.wait(1)
	button.Active = true
end)
```

Two details that matter:

**`UserOwnsGamePassAsync` is a network call and can fail.** It must be wrapped in
`pcall`. If it errors and you treat that as "does not own", you prompt someone who
already paid — which reads as trying to charge them twice.

**Returning three states, not two.** `true`, `false`, and `nil` for "the check
failed". Collapsing an error into `false` is the bug above.

`Activated` rather than `MouseButton1Click`, because `Activated` also covers gamepad
and touch. See the guide on buttons failing on mobile.

## Reacting to the result

```lua
MarketplaceService.PromptGamePassPurchaseFinished:Connect(
	function(purchasingPlayer, gamePassId, wasPurchased)
		if purchasingPlayer ~= player or gamePassId ~= PASS_ID then
			return
		end

		if wasPurchased then
			button.Text = "Thanks!"
		end
	end
)
```

Check both arguments. This event fires for prompts you did not start, and on the
server it fires for **every** player, so an unfiltered handler grants the wrong
person the wrong thing.

> [!warning]
> This event is for **UI feedback only**. Never grant the actual benefit here on
> the client — a client can fire nothing of the sort, but it also cannot be trusted
> to tell the server a purchase happened. Grant server-side, as below.

## Granting the benefit, server-side

```lua
-- ServerScriptService/PassBenefits.server.lua
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")

local PASS_ID = 123456789
local SPEED_BONUS = 8

local ownsCache = {}       -- [userId] = boolean

local function checkOwnership(player)
	local ok, owns = pcall(function()
		return MarketplaceService:UserOwnsGamePassAsync(player.UserId, PASS_ID)
	end)

	if not ok then
		warn("[Pass] check failed for", player.Name, owns)
		return false           -- fail closed; do not grant on an unknown
	end

	ownsCache[player.UserId] = owns
	return owns
end

local function applyBenefit(player)
	if not ownsCache[player.UserId] then
		return
	end

	local character = player.Character
	if not character then return end

	local humanoid = character:FindFirstChildOfClass("Humanoid")
	if humanoid then
		humanoid.WalkSpeed = 16 + SPEED_BONUS
	end
end

Players.PlayerAdded:Connect(function(player)
	checkOwnership(player)

	player.CharacterAdded:Connect(function()
		task.wait(0.1)          -- let the default WalkSpeed be applied first
		applyBenefit(player)
	end)

	if player.Character then
		applyBenefit(player)
	end
end)

-- someone buys it mid-session
MarketplaceService.PromptGamePassPurchaseFinished:Connect(
	function(player, gamePassId, wasPurchased)
		if gamePassId ~= PASS_ID or not wasPurchased then
			return
		end
		ownsCache[player.UserId] = true
		applyBenefit(player)
	end
)

Players.PlayerRemoving:Connect(function(player)
	ownsCache[player.UserId] = nil
end)
```

### Why the cache

`UserOwnsGamePassAsync` is a web request. Calling it every time a character spawns,
or on every hit in combat, is slow and will eventually be rate-limited. Check once
on join, cache the answer, and update the cache when the purchase event fires.

Clear it on `PlayerRemoving` or the table grows for the life of the server.

### Why fail closed

If the check errors, the server-side function returns `false` and grants nothing.
That is the right way round: a paying customer who has to rejoin is annoyed; a
free permanent benefit granted to everyone because Roblox's API blipped is a
broken economy.

The client-side version returns `nil` instead, because there the goal is showing an
honest message rather than making a security decision.

### Why re-apply on CharacterAdded

`WalkSpeed` lives on the `Humanoid`, and the character is rebuilt on every respawn.
Set it once on join and it is gone the first time they die.

The `task.wait(0.1)` gives Roblox's default character setup time to apply its own
`WalkSpeed` first, otherwise it can overwrite yours.

## Showing the price on the button

```lua
local ok, info = pcall(function()
	return MarketplaceService:GetProductInfoAsync(PASS_ID, Enum.InfoType.GamePass)
end)

if ok and info then
	button.Text = string.format("%s — %d R$", info.Name, info.PriceInRobux or 0)
end
```

Note **`GetProductInfoAsync`**. The older `GetProductInfo` is deprecated. Most
tutorials online still show the old name, and it will keep working for a while
before it does not.

`PriceInRobux` can be `nil` if the pass is offsale, hence the `or 0`.

<!-- OWN_EXPERIENCE -->

## Testing purchases without spending Robux

You cannot properly test a real purchase without buying it. What you can do:

- Test the **not-owned** path by using a second account that does not own the pass.
- Test the **owned** path with your own account after buying it once.
- Temporarily force the cache to `true` in Studio to check the benefit applies:
  `ownsCache[player.UserId] = true`. Remove it before publishing — an easy way to
  ship a game where everyone gets the pass for free.

Game pass purchases do not work in Studio at all. The prompt appears and does
nothing. Test in the published game.

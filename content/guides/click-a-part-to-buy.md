---
title: "Click a part to buy a game pass, with ProximityPrompt or ClickDetector"
description: Turning a world object into a shop. Two ways to do it, why ProximityPrompt is usually the better one, and the server checks that make it safe.
date: 2026-08-06
category: Monetization
kind: recipe
level: Beginner
minutes: 9
---

A pad on the floor or a vending machine that sells a game pass when a player
interacts with it. There are two mechanisms and they behave very differently on
phones.

## Option A: ProximityPrompt (recommended)

```lua
-- ServerScriptService, or a Script inside the part
local MarketplaceService = game:GetService("MarketplaceService")

local PASS_ID = 123456789
local part = workspace:WaitForChild("PassVendor")

local prompt = Instance.new("ProximityPrompt")
prompt.ActionText = "Buy Speed Pass"
prompt.ObjectText = "Vendor"
prompt.KeyboardKeyCode = Enum.KeyCode.E
prompt.HoldDuration = 0
prompt.MaxActivationDistance = 10
prompt.RequiresLineOfSight = false
prompt.Parent = part

prompt.Triggered:Connect(function(player)
	MarketplaceService:PromptGamePassPurchase(player, PASS_ID)
end)
```

Why this is the better default:

- **It works on every platform with no extra code.** Keyboard shows "E", gamepad
  shows a button, touch shows a tappable circle. A `ClickDetector` needs you to
  think about touch separately.
- **It shows the player what the interaction is** before they commit, via
  `ActionText`.
- **`MaxActivationDistance` is enforced by the engine**, so a player cannot trigger
  it from across the map.
- **`Triggered` fires on the server** with the correct `player` argument already
  filled in.

`RequiresLineOfSight = false` is worth setting — the default `true` means the prompt
vanishes when anything, including a decorative fence, is between the player and the
part.

Set `HoldDuration` to about `0.5` for anything destructive or expensive, so a
mistimed key press does not open a purchase prompt.

## Option B: ClickDetector

```lua
local MarketplaceService = game:GetService("MarketplaceService")

local PASS_ID = 123456789
local part = workspace:WaitForChild("PassVendor")

local detector = Instance.new("ClickDetector")
detector.MaxActivationDistance = 12
detector.Parent = part

detector.MouseClick:Connect(function(player)
	MarketplaceService:PromptGamePassPurchase(player, PASS_ID)
end)
```

`MouseClick` does fire on a tap despite the name, so this is not broken on mobile —
but there is no visual hint that the object is clickable, which on a phone means
most players never discover it.

Use a `ClickDetector` when the object is obviously interactive on its own (a big
labelled button model) and a prompt would look wrong.

> [!note]
> `ClickDetector` also has `MouseHoverEnter` and `MouseHoverLeave`, which are handy
> for a highlight on desktop. They never fire on touch devices, so treat any
> highlight they drive as decoration, not as the thing that tells players an object
> is usable.

## Both must be created or handled on the server

If the `Triggered` or `MouseClick` handler is in a **LocalScript**, it still works —
but then only that client knows, and anything you do in response is client-side and
private.

For a purchase prompt specifically, `PromptGamePassPurchase` can be called from
either side. Calling it from the server is simpler because you already have the
`player` argument.

For anything that changes game state, the handler must be server-side, and it must
still validate:

```lua
prompt.Triggered:Connect(function(player)
	-- the engine guarantees proximity, but check anything else yourself
	local character = player.Character
	if not character or not character:FindFirstChildOfClass("Humanoid") then
		return
	end

	if humanoidIsDead(character) then
		return
	end

	grantSomething(player)
end)
```

A `ProximityPrompt`'s distance is enforced, which is genuinely useful — but nothing
else about the player's state is.

## Making the vendor show ownership

A vendor that still says "Buy" after you have bought it looks broken. Update the
prompt per player using `Enabled`:

```lua
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")

local PASS_ID = 123456789
local prompt = workspace.PassVendor.ProximityPrompt

local function owns(player)
	local ok, result = pcall(function()
		return MarketplaceService:UserOwnsGamePassAsync(player.UserId, PASS_ID)
	end)
	return ok and result
end

prompt.Triggered:Connect(function(player)
	if owns(player) then
		-- already theirs: give them the thing instead of selling it again
		applyBenefit(player)
	else
		MarketplaceService:PromptGamePassPurchase(player, PASS_ID)
	end
end)
```

A `ProximityPrompt` is a single object shared by everyone, so you cannot show
different `ActionText` per player from the server. If you want per-player text, the
usual approach is to create the prompt on the client from a LocalScript, and keep a
server handler for anything that actually changes state.

## Anchor the vendor

An unanchored vendor part gets pushed around by players and eventually ends up in
the void, taking your shop with it.

```lua
part.Anchored = true
```

Obvious in hindsight, and it happens constantly.

<!-- OWN_EXPERIENCE -->

## Checklist

1. Vendor part is `Anchored`.
2. `ProximityPrompt` with clear `ActionText`, and `RequiresLineOfSight = false`
   unless you specifically want occlusion.
3. `Triggered` handler is on the **server**.
4. Ownership checked with `pcall`, and the owned path does something sensible rather
   than re-prompting.
5. Tested on a phone — this is the whole reason to prefer prompts over click
   detectors.

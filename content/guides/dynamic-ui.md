---
title: "Dynamic UI: one function that draws your interface from state"
description: Stop scattering Visible and Text assignments through twenty event handlers. Keep the state in one table and redraw from it.
date: 2026-08-06
category: UI
kind: learn
level: Intermediate
minutes: 12
---

Most Roblox UI code starts like this and then grows for six months:

```lua
buyButton.MouseButton1Click:Connect(function()
	shopFrame.Visible = false
	inventoryFrame.Visible = true
	coinLabel.Text = coins
	buyButton.Visible = false
	backButton.Visible = true
end)
```

Every handler pokes at half a dozen properties. Add a fourth panel and you have to
remember which of the previous three to hide, from every place that opens it. The
bugs are always the same: a frame that stays visible when it should not, a label
showing a stale number, two panels open at once.

The fix is not more careful handlers. It is one place that decides what everything
looks like.

## State in one table, one function to draw it

```lua
-- StarterPlayerScripts/Hud.client.lua
local Players = game:GetService("Players")
local player = Players.LocalPlayer

local gui = player:WaitForChild("PlayerGui"):WaitForChild("Hud")

local state = {
	screen = "closed",      -- "closed" | "shop" | "inventory"
	coins = 0,
	selectedItem = nil,
	busy = false,
}

local function render()
	-- panels: exactly one visible, decided in one place
	gui.ShopFrame.Visible = state.screen == "shop"
	gui.InventoryFrame.Visible = state.screen == "inventory"
	gui.Backdrop.Visible = state.screen ~= "closed"

	-- labels
	gui.CoinLabel.Text = string.format("%d", state.coins)

	-- buttons
	local canBuy = state.selectedItem ~= nil and not state.busy
	gui.BuyButton.Active = canBuy
	gui.BuyButton.BackgroundColor3 = canBuy
		and Color3.fromRGB(60, 140, 80)
		or Color3.fromRGB(70, 74, 80)
	gui.BuyButton.Text = state.busy and "..." or "Buy"

	gui.BackButton.Visible = state.screen ~= "closed"
end

local function setState(changes)
	for key, value in pairs(changes) do
		state[key] = value
	end
	render()
end
```

Now every handler is one line and cannot forget anything:

```lua
gui.OpenShopButton.Activated:Connect(function()
	setState({ screen = "shop" })
end)

gui.BackButton.Activated:Connect(function()
	setState({ screen = "closed", selectedItem = nil })
end)

gui.InventoryTab.Activated:Connect(function()
	setState({ screen = "inventory" })
end)
```

`render()` runs after every change, so there is exactly one description of what the UI
looks like for a given state. A panel cannot be left visible, because its visibility is
computed from `state.screen` every single time rather than toggled.

## Why this is worth the ceremony

**Adding a panel is one line per place.** Add `state.screen == "settings"` to `render`
and a handler that sets it. Nothing else changes, and no existing handler needs to
learn about it.

**Impossible states become impossible.** Two panels open at once cannot happen, because
`screen` holds one value.

**Debugging is one print.** `print(state)` tells you everything about what the UI should
be showing. Compare with the twenty-handler version, where the truth is spread across
every property of every object.

## Driving it from the server

Server values feed the same state table:

```lua
local coinsValue = player:WaitForChild("leaderstats"):WaitForChild("Coins")

coinsValue.Changed:Connect(function()
	setState({ coins = coinsValue.Value })
end)

setState({ coins = coinsValue.Value })     -- initial
```

Or with attributes, which is tidier for anything that is not a leaderboard stat:

```lua
player:GetAttributeChangedSignal("CoinMultiplier"):Connect(function()
	setState({ multiplier = player:GetAttribute("CoinMultiplier") or 1 })
end)
```

The client renders; the server decides. `state` is a mirror of server truth plus
local-only concerns like which panel is open.

## Animating transitions

`render()` sets things instantly. For movement, tween toward the state rather than
setting position directly:

```lua
local TweenService = game:GetService("TweenService")

local SHOWN = UDim2.fromScale(0.5, 0.5)
local HIDDEN = UDim2.fromScale(0.5, 1.4)

local info = TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local activeTween = nil

local function renderPanel(frame, visible)
	if visible then
		frame.Visible = true
	end

	if activeTween then
		activeTween:Cancel()
	end

	activeTween = TweenService:Create(frame, info, {
		Position = visible and SHOWN or HIDDEN,
	})

	activeTween.Completed:Connect(function(playbackState)
		if playbackState == Enum.PlaybackState.Completed and not visible then
			frame.Visible = false
		end
	end)

	activeTween:Play()
end
```

Two details:

**`Visible = true` goes before the tween, `false` after.** An invisible frame cannot
animate in, and a frame hidden immediately cannot animate out.

**Cancel the previous tween.** Rapid open/close clicks otherwise leave two tweens
fighting over `Position`, and the panel ends up somewhere between the two.

Check `playbackState` — `Completed` also fires on a cancel, and hiding the frame after a
cancelled show-tween makes the panel vanish mid-animation.

## Building lists from data

Anything list-shaped — inventory, shop, scoreboard — should be generated, not
hand-placed:

```lua
local template = gui.InventoryFrame.ItemTemplate      -- Visible = false in Studio
local container = gui.InventoryFrame.List

local function renderList(items)
	for _, child in ipairs(container:GetChildren()) do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end

	for index, item in ipairs(items) do
		local row = template:Clone()
		row.Name = item.id
		row.LayoutOrder = index
		row.NameLabel.Text = item.name
		row.CountLabel.Text = "x" .. item.count
		row.Visible = true

		row.Activated:Connect(function()
			setState({ selectedItem = item.id })
		end)

		row.Parent = container
	end
end
```

Add a `UIListLayout` to `container` and it handles positioning; `LayoutOrder` controls
the sequence. Keep the template inside the GUI with `Visible = false` so you can style
it in Studio and see your changes.

> [!warning]
> Destroying and rebuilding every row on each render is fine for tens of rows and
> wasteful for hundreds — and it drops scroll position and loses which row was
> selected. For long lists, update existing rows in place and only create or destroy
> when the count changes.

## Keeping render cheap

`render()` runs on every state change, so it must not do anything expensive: no
`WaitForChild`, no DataStore calls, no `FindFirstChild` walking the tree. Resolve all
your references once at the top of the script.

If you find yourself calling `setState` many times per frame, batch instead:

```lua
local dirty = false

local function requestRender()
	if dirty then return end
	dirty = true
	task.defer(function()
		dirty = false
		render()
	end)
end
```

`task.defer` runs at the end of the current frame, so twenty state changes in one frame
produce one redraw. Worth it only once you have measured a problem — start with the
simple version.

## Converting existing UI

You do not need to rewrite everything at once:

1. Write down every property your handlers currently set. That list becomes `render`.
2. Write down what your UI can be "in the middle of". That becomes `state`.
3. Move one panel over. Its handlers become `setState` calls.
4. Repeat. The old and new styles coexist perfectly well while you migrate.

The signal that it is working: adding a feature stops requiring you to remember what
else to turn off.

---
title: "A clock UI that shows in-game time without redrawing every frame"
description: Reading Lighting.ClockTime into a HUD label, formatting it as 12- or 24-hour, and only updating when the visible text actually changes.
date: 2026-08-06
category: UI
kind: recipe
level: Beginner
minutes: 7
---

You have a day/night cycle running and you want a clock on screen. The naive version
works and quietly wastes a lot of frames.

## The naive version

```lua
local Lighting = game:GetService("Lighting")

game:GetService("RunService").RenderStepped:Connect(function()
	label.Text = formatTime(Lighting.ClockTime)
end)
```

At 60fps this rebuilds a string and assigns `Text` sixty times a second to show a
number that changes once a minute of game time. Setting `Text` forces the UI to
re-measure and re-render that label.

## The version to use

```lua
-- LocalScript inside your HUD
local Lighting = game:GetService("Lighting")

local label = script.Parent:WaitForChild("ClockLabel")

local USE_24_HOUR = false
local lastText = nil

local function formatTime(clockTime)
	local totalMinutes = math.floor(clockTime * 60)
	local hour = math.floor(totalMinutes / 60) % 24
	local minute = totalMinutes % 60

	if USE_24_HOUR then
		return string.format("%02d:%02d", hour, minute)
	end

	local suffix = hour < 12 and "AM" or "PM"
	local display = hour % 12
	if display == 0 then
		display = 12
	end
	return string.format("%d:%02d %s", display, minute, suffix)
end

local function redraw()
	local text = formatTime(Lighting.ClockTime)
	if text ~= lastText then
		lastText = text
		label.Text = text
	end
end

Lighting:GetPropertyChangedSignal("ClockTime"):Connect(redraw)
redraw()
```

The `lastText` guard is the whole point. The signal still fires constantly, but the
expensive part — assigning `Text` — only happens when the minute rolls over.

The trailing `redraw()` sets the initial value. Without it the label shows whatever
you typed in Studio until the first change fires, which on a paused cycle is never.

## The 12-hour conversion, carefully

`hour % 12` gives `0` for both midnight and noon, and a clock reading "0:30 AM" looks
broken. The `if display == 0 then display = 12 end` line is what turns that into
"12:30 AM".

Off-by-one errors in this conversion are extremely common. Test it by jumping the
cycle to 0.1, 11.9, 12.1 and 23.9 from the Command Bar and reading what the label
says.

## Adding an icon for day and night

```lua
local icon = script.Parent:WaitForChild("PhaseIcon")

local SUN = "rbxassetid://0000000"      -- your icons
local MOON = "rbxassetid://0000000"

local lastPhase = nil

local function redrawPhase()
	local hour = Lighting.ClockTime
	local isDay = hour >= 6 and hour < 18

	if isDay ~= lastPhase then
		lastPhase = isDay
		icon.Image = isDay and SUN or MOON
	end
end
```

Same guard pattern. Setting `Image` to the value it already holds still triggers work,
and on an image it can cause a visible flicker.

## Styling it so it survives phones

```lua
label.AnchorPoint = Vector2.new(1, 0)
label.Position = UDim2.new(1, -12, 0, 12)      -- top right, 12px margin
label.Size = UDim2.new(0, 110, 0, 32)          -- fixed: text does not need to scale
label.TextScaled = false
label.TextSize = 18
label.Font = Enum.Font.GothamMedium
label.BackgroundTransparency = 0.4
label.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
label.TextColor3 = Color3.fromRGB(255, 255, 255)
```

A clock is one of the few cases where fixed `Offset` sizing is correct — it holds a
predictable short string, and it should stay a small readable badge rather than growing
to a fifth of the screen on a monitor.

`AnchorPoint` of `(1, 0)` anchors the top-**right** corner, so the negative X offset
insets it from the edge. Without that, positioning by the top-left corner puts most of
the label off screen.

Add a `UICorner` for rounded edges:

```lua
local corner = Instance.new("UICorner")
corner.CornerRadius = UDim.new(0, 6)
corner.Parent = label
```

> [!note]
> Keep the clock out of the very top strip on phones — the Roblox menu button lives
> there. Leaving `ScreenGui.IgnoreGuiInset` at its default `false` handles this for
> you.

## Showing a real-world clock instead

If you want the player's actual local time rather than game time:

```lua
local function realLocalTime()
	local t = os.date("*t")          -- client's local time
	return string.format("%02d:%02d", t.hour, t.min)
end

task.spawn(function()
	while true do
		label.Text = realLocalTime()
		task.wait(20)
	end
end)
```

`os.date("*t")` on the client returns that machine's local time, which differs per
player — fine for a clock, useless for anything you need players to agree on. For a
shared timestamp use `workspace:GetServerTimeNow()`.

Twenty seconds is a reasonable poll for a minute-resolution clock; there is no point
checking more often.

<!-- OWN_EXPERIENCE -->

## Checking it

1. Jump the time from the Command Bar and confirm the label follows:
   `game:GetService("Lighting").ClockTime = 23.98`
2. Watch it roll past midnight. `23:59 → 00:00` in 24-hour mode,
   `11:59 PM → 12:00 AM` in 12-hour.
3. Add a temporary `print` inside the `if text ~= lastText` block and confirm it fires
   about once per game minute, not once per frame. That is the whole optimisation, and
   it is worth confirming it works.

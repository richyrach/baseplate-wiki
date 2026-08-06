---
title: "A day and night cycle that looks good and stays in sync"
description: Driving Lighting.ClockTime from the server, blending ambient colour and fog through the cycle, and keeping every client on the same time.
date: 2026-08-06
category: Building
kind: recipe
level: Intermediate
minutes: 12
---

A day/night cycle is one line of code and about forty lines of art direction. The
one line:

```lua
game:GetService("Lighting").ClockTime = 14   -- 2pm
```

`ClockTime` is hours as a number from 0 to 24. `6` is dawn, `12` is noon, `18` is
dusk, `0` and `24` are midnight. There is also `TimeOfDay`, which is the same thing as
a `"HH:MM:SS"` string, and `SetMinutesAfterMidnight()` if you prefer minutes.

## The cycle, on the server

```lua
-- ServerScriptService/DayNight.server.lua
local Lighting = game:GetService("Lighting")

local DAY_LENGTH = 20 * 60      -- a full 24h cycle takes 20 real minutes
local START_HOUR = 7

task.spawn(function()
	local hoursPerSecond = 24 / DAY_LENGTH

	Lighting.ClockTime = START_HOUR

	while true do
		local dt = task.wait()
		Lighting.ClockTime = (Lighting.ClockTime + hoursPerSecond * dt) % 24
	end
end)
```

Run this on the **server**, not in a LocalScript. A client-side cycle gives every
player their own private time of day, so one player's screenshot says noon and their
friend's says midnight.

> [!note]
> `Lighting.ClockTime` is documented as *Not Replicated*, which sounds like it should
> not work from the server at all. In practice setting it server-side does drive every
> client, because it updates the underlying `TimeOfDay`. Verify this yourself with two
> clients from the **Test** tab before building on it — if you see them drift, drive
> `TimeOfDay` instead, which is the replicated property.

## Why `task.wait()` with no argument

`task.wait()` returns the time since the last frame and resumes next frame. Advancing
by `hoursPerSecond * dt` means the cycle runs at the same real-world speed regardless
of frame rate.

The naive version — `ClockTime += 0.01` then `task.wait(0.1)` — runs at whatever speed
the server happens to tick at, so the day is a different length on a busy server than
an empty one.

## Making it actually look like night

`ClockTime` alone moves the sun and gives you a dark blue night. It is functional and
flat. The look comes from moving the other `Lighting` properties along with it.

```lua
local Lighting = game:GetService("Lighting")

-- keyframes at hours of the day
local KEYS = {
	{ hour = 0,  ambient = Color3.fromRGB(18, 20, 38),   outdoor = Color3.fromRGB(28, 32, 58),
	  brightness = 1.0, fog = Color3.fromRGB(20, 24, 42), fogEnd = 400,  exposure = 0.15 },
	{ hour = 6,  ambient = Color3.fromRGB(70, 58, 62),   outdoor = Color3.fromRGB(120, 96, 92),
	  brightness = 1.8, fog = Color3.fromRGB(180, 140, 120), fogEnd = 800, exposure = 0.05 },
	{ hour = 12, ambient = Color3.fromRGB(128, 128, 128), outdoor = Color3.fromRGB(160, 160, 160),
	  brightness = 3.0, fog = Color3.fromRGB(190, 205, 220), fogEnd = 2500, exposure = 0 },
	{ hour = 18, ambient = Color3.fromRGB(92, 62, 54),   outdoor = Color3.fromRGB(140, 92, 74),
	  brightness = 1.8, fog = Color3.fromRGB(200, 130, 90), fogEnd = 900,  exposure = 0.05 },
	{ hour = 24, ambient = Color3.fromRGB(18, 20, 38),   outdoor = Color3.fromRGB(28, 32, 58),
	  brightness = 1.0, fog = Color3.fromRGB(20, 24, 42), fogEnd = 400,  exposure = 0.15 },
}

local function surrounding(hour)
	for i = 1, #KEYS - 1 do
		if hour >= KEYS[i].hour and hour <= KEYS[i + 1].hour then
			local a, b = KEYS[i], KEYS[i + 1]
			local span = b.hour - a.hour
			local alpha = span > 0 and (hour - a.hour) / span or 0
			return a, b, alpha
		end
	end
	return KEYS[1], KEYS[1], 0
end

local function applyLighting(hour)
	local a, b, alpha = surrounding(hour)

	Lighting.Ambient = a.ambient:Lerp(b.ambient, alpha)
	Lighting.OutdoorAmbient = a.outdoor:Lerp(b.outdoor, alpha)
	Lighting.FogColor = a.fog:Lerp(b.fog, alpha)
	Lighting.Brightness = a.brightness + (b.brightness - a.brightness) * alpha
	Lighting.FogEnd = a.fogEnd + (b.fogEnd - a.fogEnd) * alpha
	Lighting.ExposureCompensation = a.exposure + (b.exposure - a.exposure) * alpha
end
```

Then call it from the same loop:

```lua
while true do
	local dt = task.wait()
	Lighting.ClockTime = (Lighting.ClockTime + hoursPerSecond * dt) % 24
	applyLighting(Lighting.ClockTime)
end
```

The keyframe-and-interpolate approach is worth the extra code because tuning becomes
editing a table rather than rewriting logic. Want a longer golden hour? Add a keyframe
at 17 and 19. `Color3:Lerp` handles the blending.

Duplicating hour 0 as hour 24 makes the wrap seamless — without it, the cycle snaps at
midnight.

## Street lights that come on at dusk

```lua
local lampFolder = workspace:WaitForChild("StreetLights")

local function setLamps(on)
	for _, lamp in ipairs(lampFolder:GetDescendants()) do
		if lamp:IsA("PointLight") or lamp:IsA("SpotLight") then
			lamp.Enabled = on
		elseif lamp:IsA("BasePart") and lamp.Name == "Bulb" then
			lamp.Material = on and Enum.Material.Neon or Enum.Material.Glass
		end
	end
end

local lampsOn = nil

local function updateLamps(hour)
	local shouldBeOn = hour < 6.5 or hour > 17.5
	if shouldBeOn ~= lampsOn then
		lampsOn = shouldBeOn
		setLamps(shouldBeOn)
	end
end
```

The `lampsOn` comparison matters. Without it you are iterating every lamp in the map
every frame, which is exactly the kind of per-frame loop that makes a game lag as it
grows.

> [!warning]
> Lights are expensive. Roblox limits how many can render at once, and past that they
> pop in and out as the camera moves. If a street needs a lit look, a Neon material on
> the bulb plus a handful of real lights beats one light per lamp post.

## Letting players see the time

The cycle is on the server, so the client can just read it:

```lua
-- LocalScript
local Lighting = game:GetService("Lighting")

Lighting:GetPropertyChangedSignal("ClockTime"):Connect(function()
	label.Text = formatTime(Lighting.ClockTime)
end)
```

That fires very often — every frame the cycle advances. See the clock UI guide for the
version that only redraws when the displayed minute actually changes.

## Pausing and skipping

Expose the cycle so other systems can control it:

```lua
local paused = false

local function setTime(hour)
	Lighting.ClockTime = hour % 24
	applyLighting(Lighting.ClockTime)
end

-- inside the loop
if not paused then
	Lighting.ClockTime = (Lighting.ClockTime + hoursPerSecond * dt) % 24
	applyLighting(Lighting.ClockTime)
end
```

A round-based game usually wants time frozen during a round and advanced between them,
rather than a horror level drifting into daylight halfway through.

<!-- OWN_EXPERIENCE -->

## Tuning it

1. Set `DAY_LENGTH` short — 60 seconds — while you are adjusting the keyframes, so you
   see a full cycle quickly. Put it back afterwards.
2. Use the Command Bar to jump straight to a time you are working on:
   `game:GetService("Lighting").ClockTime = 18.5`
3. Check it with **two clients** from the Test tab and confirm both show the same time.
4. Turn `Lighting.Technology` to `Future` if your game can afford it — the same
   keyframes look considerably better, and night in particular stops looking flat.

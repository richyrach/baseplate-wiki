---
title: "TweenService vs lerp: smooth movement without a while loop"
description: When to hand movement to TweenService, when to interpolate yourself, and why tweening a Model does not work.
date: 2026-08-06
category: Animation
kind: recipe
level: Beginner
minutes: 9
---

You want something to move smoothly instead of teleporting. There are two tools and
the choice is genuinely situational.

- **`TweenService`** — you know the start, the end, and the duration up front.
- **Manual interpolation (`Lerp`)** — the target can change while the motion is
  running, or the motion depends on something live.

## TweenService: the common case

```lua
local TweenService = game:GetService("TweenService")

local part = workspace.Platform

local info = TweenInfo.new(
	2,                              -- seconds
	Enum.EasingStyle.Quad,          -- shape of the acceleration
	Enum.EasingDirection.InOut,     -- where the easing applies
	0,                              -- repeat count
	false,                          -- reverses
	0                               -- delay
)

local tween = TweenService:Create(part, info, {
	CFrame = part.CFrame * CFrame.new(0, 20, 0),
})

tween:Play()
```

Everything after the duration is optional — `TweenInfo.new(2)` is valid and gives
you a sensible default.

`Create` takes the object, the info, and a table of **target property values**. Any
numeric-ish property works: `CFrame`, `Position`, `Size`, `Transparency`,
`BackgroundColor3`, `UDim2`, `Rotation`.

### Waiting for it

```lua
tween.Completed:Connect(function(playbackState)
	if playbackState == Enum.PlaybackState.Completed then
		print("arrived")
	end
end)

-- or block the current thread
tween:Play()
tween.Completed:Wait()
```

Check the `playbackState`. `Completed` also fires when a tween is cancelled, and
treating a cancellation as a successful arrival causes subtle bugs — a door that
reports itself open after being interrupted halfway.

### Easing, briefly

- `Linear` — constant speed. Mechanical: lifts, conveyor belts.
- `Quad` / `Cubic` with `InOut` — accelerate then decelerate. The default choice for
  almost everything; reads as natural.
- `Back` — overshoots slightly then settles. Good on UI appearing.
- `Elastic` / `Bounce` — very obvious. Fine for a cartoon effect, tiring anywhere else.

If you are unsure, `Quad` + `InOut` is right more often than not.

## The Model problem

This does not work:

```lua
TweenService:Create(workspace.Door, info, { CFrame = target })   -- errors
```

A `Model` has no `CFrame` property. Tweens animate properties, and a model's
position is a pivot, not a property.

Two workarounds:

**Tween the PrimaryPart and let welds carry the rest.** This is the good one:

```lua
local model = workspace.Door
model.PrimaryPart = model:WaitForChild("Hinge")

-- everything else is welded to Hinge, and unanchored
TweenService:Create(model.PrimaryPart, info, {
	CFrame = model.PrimaryPart.CFrame * CFrame.Angles(0, math.rad(90), 0),
}):Play()
```

For this to work, the `PrimaryPart` must be `Anchored` and every other part
unanchored and welded to it. The tween moves the anchored root; the welds drag the
rest along.

**Drive `PivotTo` yourself** — the manual approach below.

## Manual interpolation

```lua
local RunService = game:GetService("RunService")

local function moveModel(model, target, seconds)
	local start = model:GetPivot()
	local elapsed = 0

	local connection
	connection = RunService.Heartbeat:Connect(function(dt)
		elapsed += dt
		local alpha = math.min(elapsed / seconds, 1)
		model:PivotTo(start:Lerp(target, alpha))

		if alpha >= 1 then
			connection:Disconnect()
		end
	end)
end
```

`CFrame:Lerp(goal, alpha)` interpolates position and rotation together. `alpha` runs
0 to 1. `Vector3` and `Color3` have `Lerp` too, and plain numbers use
`a + (b - a) * alpha`.

Note `connection:Disconnect()`. A `Heartbeat` connection you never disconnect runs
for the lifetime of the server, and a few hundred of them is a real performance
problem.

## The pattern for a target that keeps moving

This is where TweenService cannot help, because the destination is not known when
the motion starts — a camera following a player, a turret tracking a target:

```lua
local RunService = game:GetService("RunService")

local SMOOTHING = 5

RunService.Heartbeat:Connect(function(dt)
	local goal = target.Position
	local current = follower.Position

	local alpha = 1 - math.exp(-SMOOTHING * dt)
	follower.Position = current:Lerp(goal, alpha)
end)
```

The `1 - math.exp(-k * dt)` form is worth knowing. The naive version —
`alpha = SMOOTHING * dt` — gives you different smoothing at different frame rates,
so the motion feels different on a fast machine than a slow one. The exponential
form is frame-rate independent, which is why it turns up in camera code everywhere.

## Which event to use

- **`Heartbeat`** — after physics. Right for most logic and for moving anchored
  things.
- **`RenderStepped`** — before the frame is drawn, client only. Right for camera work
  and anything that must be exactly in sync with what is rendered. Keep the work here
  small; it runs before every frame and delays it.
- **`PreSimulation` / `PostSimulation`** — the newer names in this family, worth
  preferring in new code as the older ones are gradually deprecated.

## Stopping and reusing tweens

```lua
tween:Pause()
tween:Cancel()   -- resets to the start
```

`Cancel` snaps the property back. `Pause` leaves it mid-motion.

A tween created for one journey is not reusable for a different destination — create
a new one. Creating tweens is cheap; caching them and mutating their goals is not
supported.

> [!warning]
> Tweening a property that physics also controls means both fight for it. Tweening
> `Position` on an unanchored part produces stutter as the tween sets it and physics
> moves it back. Anchor anything you tween, or move it with physics constraints
> instead.

<!-- OWN_EXPERIENCE -->

## Quick decision guide

| Situation | Use |
|---|---|
| Known start and end, fixed duration | `TweenService` |
| A GUI element appearing or moving | `TweenService` |
| A model that is welded to a PrimaryPart | `TweenService` on the PrimaryPart |
| Target changes while moving | manual `Lerp` on `Heartbeat` |
| Camera following something | manual `Lerp` with `1 - math.exp(-k * dt)` |
| An unanchored physical object | neither — use constraints and forces |

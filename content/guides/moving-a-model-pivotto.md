---
title: "Moving a model without it exploding: PrimaryPart and PivotTo"
description: Setting a model's position part by part tears welded assemblies apart. Move the whole thing at once instead.
date: 2026-08-06
category: Building
kind: recipe
level: Intermediate
minutes: 8
---

You have a model — a car, a door, a platform — and you need to move it in a
script. You try the obvious thing:

```lua
model.Position = Vector3.new(0, 10, 0)
```

That errors, because a `Model` has no `Position` property. So you loop over the
parts and move each one, and the model arrives at its destination in pieces.

The fix is to move the model as a single unit.

## The answer

```lua
local model = workspace.Door

-- absolute placement
model:PivotTo(CFrame.new(10, 5, -20))

-- relative to where it already is
model:PivotTo(model:GetPivot() * CFrame.new(0, 5, 0))

-- rotate 90 degrees around its own centre
model:PivotTo(model:GetPivot() * CFrame.Angles(0, math.rad(90), 0))
```

`PivotTo` moves every part in the model together and preserves the offsets between
them, so welds survive.

## Set a PrimaryPart first

A model's pivot is the CFrame of its `PrimaryPart`. If `PrimaryPart` is `nil`,
Roblox falls back to the centre of the model's bounding box — which shifts if you
add or remove parts, and is rarely where you actually want the origin.

Set it explicitly:

```lua
model.PrimaryPart = model:WaitForChild("Base")
```

You can set it in Studio too: select the model, and in Properties click the
`PrimaryPart` field, then click the part you want in the viewport.

Pick something meaningful. For a car, the chassis base. For a door, the hinge edge
— then rotating the pivot rotates the door around its hinge rather than its middle,
which is almost always what you wanted.

> [!note]
> `Model:GetPivot()` returns the current pivot CFrame, and `PivotTo` sets it. They
> are a matched pair, and `GetPivot() * offset` is the idiom for "move relative to
> where it is now."

## Order matters: multiplication is not commutative

```lua
local pivot = model:GetPivot()

model:PivotTo(pivot * CFrame.new(0, 0, -10))   -- 10 studs along the model's OWN forward
model:PivotTo(CFrame.new(0, 0, -10) * pivot)   -- 10 studs along the WORLD's -Z
```

`pivot * offset` applies the offset in the model's local space. `offset * pivot`
applies it in world space. Getting these the wrong way round produces a model that
moves in a strange direction when rotated, and is worth checking first when
movement looks almost-but-not-quite right.

## MoveTo is a different tool

```lua
model:MoveTo(Vector3.new(0, 0, 0))
```

`MoveTo` places the model's centre at a position, but it also shifts the model
**upward** if something is already there, to avoid overlapping. That makes it handy
for dropping something onto terrain and unusable when you need an exact position.

If a model keeps ending up higher than you asked, `MoveTo` is why. Use `PivotTo`.

> [!warning]
> `Model:SetPrimaryPartCFrame()` appears in a lot of older tutorials. It is
> deprecated in favour of `PivotTo`, and it had rounding behaviour that could drift
> a model slightly over many calls. New code should use `PivotTo`.

## Moving smoothly

`PivotTo` is instant. For animated movement, tween a value and apply it each frame:

```lua
local RunService = game:GetService("RunService")

local function slideModel(model, targetCFrame, seconds)
	local startCFrame = model:GetPivot()
	local elapsed = 0

	local connection
	connection = RunService.Heartbeat:Connect(function(dt)
		elapsed += dt
		local alpha = math.min(elapsed / seconds, 1)
		model:PivotTo(startCFrame:Lerp(targetCFrame, alpha))

		if alpha >= 1 then
			connection:Disconnect()
		end
	end)
end

slideModel(workspace.Platform, CFrame.new(0, 20, 0), 2)
```

`CFrame:Lerp` interpolates position and rotation together, so this works for
rotating movement as well as straight lines.

You cannot pass a `Model` to `TweenService` directly, because tweens animate
*properties* and the pivot is not one. The usual workaround is to tween the
`PrimaryPart`'s `CFrame` and weld everything else to it — the welds carry the rest
of the model along. That is often simpler than the loop above, and it gets you
TweenService's easing styles for free.

## Anchored, unanchored, and which to use

- **Anchored root, `PivotTo` each frame** — full control, no physics interference.
  Right for doors, lifts, moving platforms.
- **Unanchored root, physics constraints** — right for vehicles and anything that
  should collide and be pushed around.

Calling `PivotTo` repeatedly on an *unanchored* assembly fights the physics solver:
you set a position, physics moves it, you set it again. The result stutters. If you
are driving movement from a script, anchor the root.

<!-- OWN_EXPERIENCE -->

## If the model still comes apart

1. Is `PrimaryPart` set, and is it one of the parts actually welded to the rest?
2. Are the welds `WeldConstraint`s created **after** all parts were positioned?
3. Is any part still `Anchored` while the root is not? That part will stay behind.
4. Are you calling `PivotTo` on the `Model` — not on a part inside it?

---
title: "Why your car flips, sinks, or drives like it's on ice"
description: Vehicle handling problems nearly always trace back to mass, centre of gravity, or friction. Three properties, in the order to check them.
date: 2026-08-06
category: Vehicles
kind: learn
level: Intermediate
minutes: 11
---

A car that flips on every corner, sinks into the road, or slides like the map is
made of glass is almost never a scripting problem. It is physics doing exactly what
the numbers you gave it say it should.

There are three numbers, and checking them in this order solves most vehicle
handling complaints.

## 1. Centre of gravity is too high

A vehicle flips because its mass is high above its wheels. Roblox derives the
centre of mass from the parts you built with, and a body made of large blocks
sitting on top of small wheels puts that centre well above the axle line.

The fix that works, and that real vehicle physics uses too, is to add weight low
down:

```lua
local ballast = Instance.new("Part")
ballast.Name = "Ballast"
ballast.Size = Vector3.new(4, 0.4, 8)
ballast.Transparency = 1
ballast.CanCollide = false
ballast.Massless = false
ballast.CustomPhysicalProperties = PhysicalProperties.new(
	12,    -- density: heavy
	0.3,   -- friction
	0,     -- elasticity
	1,     -- friction weight
	1      -- elasticity weight
)
ballast.CFrame = chassis.CFrame * CFrame.new(0, -1.2, 0)
ballast.Parent = vehicle

local weld = Instance.new("WeldConstraint")
weld.Part0 = chassis
weld.Part1 = ballast
weld.Parent = chassis
```

An invisible, non-colliding, dense slab welded below the chassis drags the centre
of mass down without changing how the car looks or collides. Tune the density: too
little and it still rolls, too much and it feels like it is bolted to the ground.

> [!note]
> Make the bodywork lighter as well as the floor heavier. Set
> `CustomPhysicalProperties` with a low density on roof and shell parts, or mark
> purely decorative parts `Massless = true` so they contribute no mass at all.

## 2. Parts are Massless, or the wrong parts are

`Massless = true` makes a part contribute no mass to its assembly. It is genuinely
useful for detail parts — mirrors, spoilers, badges — that should not affect
handling.

It causes two distinct bugs when misapplied:

- **Everything massless.** The vehicle weighs almost nothing, gets thrown around by
  the slightest collision, and bounces off kerbs.
- **The wheels massless.** Wheels need mass to press into the road. Massless wheels
  produce no grip, and the car slides.

Audit it:

```lua
for _, part in ipairs(vehicle:GetDescendants()) do
	if part:IsA("BasePart") then
		print(string.format("%-20s mass=%.2f massless=%s",
			part.Name, part:GetMass(), tostring(part.Massless)))
	end
end
```

Run that in the Command Bar with the vehicle selected. Any wheel or chassis part
reporting a mass near zero is a problem.

## 3. Friction is wrong on the wheels or the road

Sliding is a friction problem, and friction is a negotiation between two surfaces —
so the road matters as much as the tyre.

```lua
wheel.CustomPhysicalProperties = PhysicalProperties.new(
	0.7,   -- density
	2,     -- friction: high, tyres grip
	0,     -- elasticity: 0, tyres do not bounce
	100,   -- friction weight: dominate the contact
	1
)
```

The fourth argument, **friction weight**, is the one people miss. It decides whose
friction value wins when two surfaces touch. Setting it high on the wheel means the
tyre's grip dominates whatever the road says, which is what you want — otherwise a
slippery road surface overrides your careful tyre tuning.

Elasticity should be `0` on wheels. Any bounce turns small bumps into launches.

## Sinking through the road

If the car falls through geometry, it is almost always one of:

- **The road is not `Anchored`.** Unanchored road parts get pushed by the car.
- **`CanCollide = false`** on the wheels or the road part.
- **Very thin road parts.** A part under about 0.5 studs thick can be passed
  through by a fast-moving object between physics steps. Make roads at least one
  stud thick.
- **Very high speed.** Fast objects tunnel through thin geometry. Thicker
  collision surfaces are the practical fix.

## Steering that feels wrong

Two distinct complaints here:

**Turns too sharply at speed** — the steering angle should reduce as speed rises.
Real cars do this and it is most of what makes a vehicle feel controlled:

```lua
local MAX_ANGLE = 35
local MIN_ANGLE = 8
local FALLOFF_SPEED = 90

local function steerAngleFor(speed)
	local t = math.clamp(speed / FALLOFF_SPEED, 0, 1)
	return MAX_ANGLE + (MIN_ANGLE - MAX_ANGLE) * t
end
```

**Snaps back to centre instantly** — interpolate toward the target angle instead of
setting it:

```lua
currentAngle += (targetAngle - currentAngle) * math.min(dt * 6, 1)
```

The `math.min(dt * 6, 1)` guard matters: on a frame with a long delta, `dt * 6` can
exceed 1 and overshoot the target, which produces a visible jitter.

## If you are using A-Chassis

A-Chassis is the most common community chassis and it has its own tuning file,
usually `A-Chassis Tune` inside the vehicle model. Its values override a lot of
what you would otherwise set by hand.

The values worth looking at first:

- `Tune.WeightBrickSize` and `Tune.Weight` — the ballast concept above, built in.
- `Tune.CenterOfGravity` — moves the centre of mass directly.
- `Tune.WheelFrictionWeight`, `Tune.FrictionMultiplier` — grip.
- `Tune.SteerInner` / `Tune.SteerOuter` and `Tune.SteerDecay` — the speed falloff
  above, built in.

If A-Chassis is installed, tune there rather than setting `CustomPhysicalProperties`
manually — otherwise you have two systems fighting over the same properties, and the
result depends on which ran last.

> [!warning]
> Check which version of A-Chassis you have before following any tutorial. Tune
> value names moved between 6.x and later releases, and a guide written for the
> wrong version will have you editing values that do not exist.

<!-- OWN_EXPERIENCE -->

## The diagnostic order

1. Print the mass of every part. Anything unexpectedly near zero is suspect.
2. Add or increase low ballast until it stops flipping. This fixes most of it.
3. Raise wheel friction and friction weight until it stops sliding.
4. Set wheel elasticity to `0`.
5. Confirm the road is anchored, collidable, and at least a stud thick.
6. Only then start adjusting steering feel — tuning steering on a car with a bad
   centre of gravity is wasted effort.

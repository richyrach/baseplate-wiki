---
term: Anchored
category: Building
summary: Freezes a part in place. Physics ignores it entirely, which makes it both correct and cheap for scenery.
---

`Anchored` is a boolean on every `BasePart`. When it is `true`, physics does not move
that part — it does not fall, cannot be pushed, and is not simulated.

```lua
part.Anchored = true
```

## Why it matters twice

**Correctness.** An unanchored part falls the instant physics starts. This is why a
build that looks perfect in Studio collapses when you press Play: edit mode does not
run physics, so nothing was holding it up.

**Performance.** Anchored parts are essentially free. Unanchored parts are bodies the
physics solver must resolve every frame. A map with thousands of unanchored decorative
parts is one of the most common causes of a game that runs badly for no visible
reason.

Auditing a map takes one loop:

```lua
local total, loose = 0, 0
for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("BasePart") then
		total += 1
		if not d.Anchored then loose += 1 end
	end
end
print(total, "parts,", loose, "unanchored")
```

## The interaction people get wrong

**Anchored beats welded.** If any part in a welded assembly is anchored, the whole
assembly is effectively immovable, because the weld ties it to something that cannot
move.

This is the number one cause of "my welded vehicle will not move." One wheel is still
anchored from when it was being built.

```lua
-- unanchor everything in a model that is meant to move
for _, part in ipairs(model:GetDescendants()) do
	if part:IsA("BasePart") then
		part.Anchored = false
	end
end
```

> [!warning]
> Setting `Anchored = false` on a large assembly at runtime hands the whole thing to
> the physics engine at once. If parts are slightly intersecting, they will violently
> push apart. Position accurately before unanchoring.

## Anchored versus Massless versus CanCollide

Three properties that all sound like they might stop a part moving, and do different
things:

| Property | Effect |
|---|---|
| `Anchored = true` | not simulated at all; immovable |
| `Massless = true` | simulated, but contributes no mass to its assembly |
| `CanCollide = false` | simulated and has mass, but passes through things |

`Massless` is for detail parts — mirrors, badges — that should not affect how a
vehicle handles. It does **not** stop them falling; a massless unanchored part still
drops.

## Driving movement on an anchored part

Anchored parts can still be moved by script, which is exactly what you want for
doors, lifts and platforms:

```lua
part.Anchored = true
part.CFrame = part.CFrame * CFrame.new(0, 5, 0)
```

Because physics is not fighting you for control, scripted movement on an anchored part
is smooth and exact. The same code on an unanchored part stutters, as the script sets
a position and physics immediately moves it somewhere else.

For a whole model, move the model rather than the parts — see `PivotTo`.

## In Studio

Select any number of parts and tick **Anchored** once in the Properties panel; it
applies to the entire selection. A checkbox showing a mixed state means some of the
selection is anchored and some is not, which for scenery is a bug you have just found.

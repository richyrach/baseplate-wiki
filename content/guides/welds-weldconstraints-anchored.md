---
title: "Welds, WeldConstraints and Anchored: why your build falls apart on Play"
description: Your model looks perfect in Studio and collapses the instant you press Play. There are three ways to hold parts together and they behave very differently.
date: 2026-08-06
category: Building
kind: learn
level: Beginner
minutes: 10
---

You spend an hour building something out of forty parts. It looks exactly right.
You press Play and it collapses into a heap on the floor.

Nothing is broken. Studio's edit mode does not run physics, so nothing was holding
those parts together in the first place — you were looking at forty separate
objects that happened to be sitting in the right positions.

The instant physics starts, gravity applies to each one independently.

## The three options, and when each is right

| Option | Parts can move | Held together | Use it for |
|---|---|---|---|
| `Anchored = true` | no | n/a — frozen in place | walls, floors, scenery, anything static |
| `WeldConstraint` | yes, as one body | yes | doors, vehicles, anything that moves |
| Grouping into a Model | yes | **no** | organisation only |

That last row is the trap. Grouping parts into a Model organises your Explorer and
does absolutely nothing physically. A Model is a folder, not glue.

## Anchored: for anything that should never move

If a part is scenery, anchor it. That is the whole answer.

```lua
for _, descendant in ipairs(workspace.Building:GetDescendants()) do
	if descendant:IsA("BasePart") then
		descendant.Anchored = true
	end
end
```

An anchored part is completely immovable by physics. It does not fall, it cannot
be pushed, and it costs the engine essentially nothing because it is never
simulated.

This matters for performance as much as correctness. A thousand anchored parts are
cheap. A thousand unanchored parts are a thousand bodies the physics engine has to
solve every frame, and it is one of the most common reasons a map runs badly.

> [!note]
> In Studio you can select every part in a model and tick **Anchored** once in the
> Properties panel — it applies to the whole selection. For a whole map, the loop
> above run from the Command Bar is faster.

## WeldConstraint: for things that move as one piece

A `WeldConstraint` locks two parts' relative positions. Move one, the other
follows.

```lua
local function weld(part0, part1)
	local w = Instance.new("WeldConstraint")
	w.Part0 = part0
	w.Part1 = part1
	w.Parent = part0
	return w
end
```

Weld every part to **one** part — usually the largest, or the one you will move
later:

```lua
local model = workspace.Door
local root = model.PrimaryPart or model:FindFirstChildWhichIsA("BasePart")

for _, part in ipairs(model:GetDescendants()) do
	if part:IsA("BasePart") and part ~= root then
		part.Anchored = false
		weld(root, part)
	end
end

root.Anchored = false
```

Two things about this that catch people out:

**Position at the moment of welding is what gets locked.** A `WeldConstraint`
records the offset between the two parts when it is created and enabled. Create
the weld first and move the part afterwards, and it will snap back or drag its
partner with it. Position everything, *then* weld.

**Anchored beats welded.** If any part in a welded assembly is anchored, the
entire assembly is effectively anchored, because the weld ties it to something
immovable. This is the single most common "my welded car won't move" cause: one
wheel is still anchored from when you were building it.

## Weld vs WeldConstraint

There is an older `Weld` object as well, and the difference matters.

- **`WeldConstraint`** has `Part0` and `Part1` and works out the offset itself.
  This is what you want almost always.
- **`Weld`** has `Part0`, `Part1`, `C0` and `C1` — explicit CFrame offsets you set
  yourself. Powerful, fiddly, and easy to get wrong. Mostly seen in older vehicle
  code.

If you are writing something new, use `WeldConstraint`.

> [!warning]
> Studio's **Weld** button under the Model tab, and the `Surface` properties
> (`SurfaceType`, `Studs`, `Inlet`) are a third and much older system. Mixing
> surface welds with WeldConstraints produces assemblies that behave differently
> depending on how they were assembled, which is miserable to debug. Pick one
> approach per model.

## Moving a welded model

Once parts are welded, do not move them individually — that fights the welds.
Move the model as a unit:

```lua
local model = workspace.Door
model:PivotTo(model:GetPivot() * CFrame.Angles(0, math.rad(90), 0))
```

`PivotTo` moves the whole model and everything welded to it, preserving the
internal offsets. It needs a `PrimaryPart` set on the model, or it uses the
model's bounding-box centre.

`Model:MoveTo(position)` also exists and additionally tries to avoid overlapping
other objects by shifting upward — convenient for placing things on terrain,
unhelpful when you want an exact position.

## The checklist when a build collapses

1. Is every scenery part **Anchored**? Select the model, check the Properties
   panel shows Anchored ticked rather than showing a mixed state.
2. For things that should move: is exactly one part the root, and is every other
   part welded to it?
3. Is any part in the moving assembly still anchored? One is enough to freeze the
   lot.
4. Were the welds created **after** everything was positioned?
5. Are you moving the model with `PivotTo`, rather than setting one part's
   position?

<!-- OWN_EXPERIENCE -->

## Checking your work without publishing

Press Play, then immediately switch to the **Explorer** and watch the model while
physics runs. You will see instantly whether parts are separating, and which ones.

For a faster loop, select a part in the running game and look at its `Anchored`
and `AssemblyLinearVelocity` properties. A part that should be still and has a
non-zero velocity is telling you exactly what is wrong.

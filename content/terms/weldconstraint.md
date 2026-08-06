---
term: WeldConstraint
aka: WeldConstraints
category: Building
summary: Locks two parts' relative positions so they move as one body. The modern way to hold an assembly together.
---

A `WeldConstraint` fixes the relative position of two parts. Move one and the other
follows.

```lua
local weld = Instance.new("WeldConstraint")
weld.Part0 = chassis
weld.Part1 = wheelHousing
weld.Parent = chassis
```

It records the offset between the two parts **at the moment it is created and
enabled**, and works it out itself — you do not supply any CFrames.

## The star pattern

Weld everything to one root part rather than chaining part to part:

```lua
local root = model.PrimaryPart or model:FindFirstChildWhichIsA("BasePart")

for _, part in ipairs(model:GetDescendants()) do
	if part:IsA("BasePart") and part ~= root then
		local w = Instance.new("WeldConstraint")
		w.Part0 = root
		w.Part1 = part
		w.Parent = root
	end
end
```

Chains work but are harder to reason about, and a single broken link splits the
assembly in two.

## The three things that break it

**Welding before positioning.** The offset is captured at creation. Create the weld,
then move a part, and it snaps back or drags its partner along. Position everything
first.

**A part left anchored.** If any part in the assembly is `Anchored`, the whole
assembly is effectively immovable — the weld ties it to something that cannot move.
This is the most common cause of a welded vehicle that will not budge.

**Moving individual parts afterwards.** Once welded, move the model as a unit with
`PivotTo`, not by setting one part's `CFrame`.

## WeldConstraint vs Weld

- **`WeldConstraint`** — `Part0`, `Part1`, offset computed automatically. Use this.
- **`Weld`** — `Part0`, `Part1`, plus explicit `C0` and `C1` CFrame offsets you set
  yourself. Powerful, fiddly, and mostly encountered in older vehicle code.

There is also a much older surface-based system (`SurfaceType`, studs and inlets) and
Studio's Model-tab **Weld** button. Mixing systems in one model produces assemblies
that behave differently depending on assembly order, which is miserable to debug.
Pick one approach per model.

> [!note]
> `WeldConstraint` has an `Enabled` property. Setting it to `false` releases the
> connection without destroying the object, which is a clean way to make something
> break apart on demand and be reassembled later.

## Checking your welds at runtime

```lua
for _, d in ipairs(model:GetDescendants()) do
	if d:IsA("WeldConstraint") then
		print(d.Part0 and d.Part0.Name, "<->", d.Part1 and d.Part1.Name,
			"enabled:", d.Enabled)
	end
end
```

A `nil` on either side is a weld doing nothing — usually because the part it pointed
at was destroyed or renamed.

## Related

`Anchored` for anything static, which is cheaper and simpler than welding a building
together. Welds are for assemblies that need to **move** as one piece: doors,
vehicles, platforms. Scenery should just be anchored.

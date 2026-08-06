---
term: UDim2
category: UI
summary: The two-part size and position type for GUI objects. Scale is a fraction of the parent, Offset is fixed pixels.
---

Every `Size` and `Position` on a GUI object is a `UDim2`, and it carries two numbers
per axis:

```lua
UDim2.new(xScale, xOffset, yScale, yOffset)
```

- **Scale** — a fraction of the parent. `0.5` is half the parent's width, whatever
  that happens to be.
- **Offset** — pixels. `400` is 400 pixels on every screen.

The distinction is the single biggest cause of UI that works on a monitor and breaks
on a phone. A 400-pixel panel is a fifth of a 1920px screen and wider than a 360px
one.

```lua
frame.Size = UDim2.new(0, 400, 0, 300)      -- fixed: breaks on small screens
frame.Size = UDim2.new(0.5, 0, 0.3, 0)      -- proportional: adapts
```

## The shorthand constructors

```lua
UDim2.fromScale(0.5, 0.3)     -- scale only
UDim2.fromOffset(400, 300)    -- pixels only
```

Prefer these when you are using only one system — they say which one you meant, so a
reader does not have to count zeroes.

## Mixing them is normal

Combining both on one axis is usually the right answer, not a compromise:

```lua
-- 80% of the parent's width minus a 20px margin, fixed 44px tall
frame.Size = UDim2.new(0.8, -20, 0, 44)
```

Width adapts to the screen; height stays a comfortable tap target. Negative offsets
are valid and are the standard way to express a margin.

## Rules of thumb

Use **Scale** for anything that should grow with the screen: panels, columns, overall
layout, gaps between large blocks.

Use **Offset** for anything that should stay a fixed physical size: borders, small
icons, minimum tap heights, padding of a few pixels.

## Position is measured from the top-left

By default `Position` places an object's **top-left corner**, so this does not centre
anything:

```lua
frame.Position = UDim2.fromScale(0.5, 0.5)   -- corner at centre
```

`AnchorPoint` changes which point of the object is being positioned:

```lua
frame.AnchorPoint = Vector2.new(0.5, 0.5)
frame.Position = UDim2.fromScale(0.5, 0.5)   -- actually centred
```

Note that `AnchorPoint` is a `Vector2`, not a `UDim2` — it is always a fraction.

## Arithmetic

`UDim2` values add and subtract, which is handy for tween targets:

```lua
local hidden = UDim2.fromScale(0.5, 1.2)
local shown = hidden - UDim2.fromScale(0, 0.5)
```

Each component adds independently, so scale adds to scale and offset to offset — they
do not convert into each other.

## Related

`UDim` is the single-axis version, used by `UIPadding`, `UICorner` and layout
constraints:

```lua
local padding = Instance.new("UIPadding")
padding.PaddingLeft = UDim.new(0, 12)     -- 12 fixed pixels
```

`UIAspectRatioConstraint` is what stops Scale on both axes distorting an element, and
`TextScaled` with a `UITextSizeConstraint` is the equivalent problem for text.

---
title: "Scale vs Offset: building a GUI that survives phone screens"
description: Your menu is perfect on your monitor and unusable on a phone. The cause is almost always Offset, and the fix is one property.
date: 2026-08-06
category: UI
kind: learn
level: Beginner
minutes: 9
---

You build a menu in Studio. It looks right. A player opens it on a phone and the
buttons are off the edge of the screen, or the whole panel is a postage stamp in
one corner.

The cause is nearly always the same: the GUI was sized in **Offset** — fixed pixels
— on a screen that is a different number of pixels wide.

## The two numbers in every UDim2

Every `Size` and `Position` on a GUI object is a `UDim2`, and it holds two values
per axis:

```lua
UDim2.new(xScale, xOffset, yScale, yOffset)
```

- **Scale** is a fraction of the parent. `0.5` means half the parent's width,
  whatever that is.
- **Offset** is a number of pixels. `400` means 400 pixels, on every device.

A 400-pixel-wide panel is 21% of a 1920px monitor and 111% of a 360px phone. Same
number, completely different result. That is the entire bug.

```lua
-- fragile: fixed pixels
frame.Size = UDim2.new(0, 400, 0, 300)

-- adapts: half the parent, 30% tall
frame.Size = UDim2.new(0.5, 0, 0.3, 0)
```

There are shorthand constructors that make the intent obvious:

```lua
frame.Size = UDim2.fromScale(0.5, 0.3)     -- scale only
frame.Size = UDim2.fromOffset(400, 300)    -- pixels only
```

## Use Scale for layout, Offset for details

Scale is not always right. The rule that works in practice:

**Scale** for anything that should grow with the screen — panels, columns, the
overall menu, spacing between big blocks.

**Offset** for things that should stay a fixed physical size — a 2-pixel border, an
8-pixel gap, an icon that should not become a blurry giant on a 4K monitor.

Mixing them on one axis is fine and often exactly right:

```lua
-- 80% of the parent's width, minus 20 pixels of margin
frame.Size = UDim2.new(0.8, -20, 0, 44)
```

That is a full-width-ish bar with a fixed 44-pixel height — the height stays
tappable on a phone instead of collapsing to nothing.

## AnchorPoint: the missing half of positioning

`Position` sets where an object's **top-left corner** goes by default. So this does
not centre anything:

```lua
frame.Position = UDim2.fromScale(0.5, 0.5)   -- top-left corner at the centre
```

`AnchorPoint` changes which point of the object is being positioned. It runs from
`(0, 0)` for top-left to `(1, 1)` for bottom-right:

```lua
frame.AnchorPoint = Vector2.new(0.5, 0.5)
frame.Position = UDim2.fromScale(0.5, 0.5)   -- now genuinely centred
```

This is the fix for "my GUI is roughly centred but visibly off," and it scales
correctly on every screen, which manual pixel nudging does not.

## Keeping proportions with UIAspectRatioConstraint

Scale on both axes distorts, because screens are not all the same shape. A square
icon becomes a rectangle on a wide phone.

```lua
local constraint = Instance.new("UIAspectRatioConstraint")
constraint.AspectRatio = 1        -- width / height
constraint.Parent = frame
```

Now set the size on one axis and let the constraint compute the other:

```lua
frame.Size = UDim2.fromScale(0.3, 0)   -- height follows from the ratio
```

This is how you get a card or an avatar that keeps its shape everywhere. For a
16:9 panel, set `AspectRatio = 16/9`.

## Text needs its own attention

Text does not scale with its container. A label sized in Scale gets bigger; the
text inside stays the same pixel height and starts overflowing or looking lost.

```lua
label.TextScaled = true
```

`TextScaled` makes the text fill the label. Add a minimum so it does not become
unreadable in a small container:

```lua
local size = Instance.new("UITextSizeConstraint")
size.MinTextSize = 12
size.MaxTextSize = 28
size.Parent = label
```

Without `MaxTextSize`, a big label on a monitor produces comically large text.
Without `MinTextSize`, a small one produces text nobody can read.

## The status bar eats your top row

On phones, the top of the screen has the Roblox button and system UI over it. A
frame at `Position = UDim2.fromScale(0, 0)` can end up underneath.

```lua
screenGui.IgnoreGuiInset = false   -- default: the safe area is respected
```

Leaving `IgnoreGuiInset` at `false` keeps your GUI below the inset. Set it to
`true` only for full-screen backgrounds that are meant to run edge to edge, and
keep interactive elements out of the top strip either way.

## Testing without a phone

Studio has this built in and it takes ten seconds:

1. Open the **Test** tab.
2. Click **Device**.
3. Pick a phone from the emulator list — a small one like an older iPhone is the
   harshest useful test.

Check both orientations. Landscape phones are short, which breaks vertical layouts
that assumed plenty of height.

> [!note]
> The device emulator changes the viewport, which is what actually matters for
> UDim2 maths. It does not emulate touch input precisely, so a button that looks
> right here can still fail to respond on a real phone for unrelated reasons.

## Minimum tap size

A button that is 20 pixels tall is comfortable with a mouse and nearly impossible
with a thumb. Keep interactive elements at least around 44 pixels on their shortest
side:

```lua
button.Size = UDim2.new(0.4, 0, 0, 48)   -- flexible width, fixed tappable height
```

This is why the mixed Scale/Offset pattern earns its keep: the width adapts, the
height stays usable.

## The audit

Open your GUI and check each object:

1. Any `Size` or `Position` with a large Offset number and a `0` Scale is suspect.
2. Anything meant to be centred should have an `AnchorPoint` other than `(0, 0)`.
3. Anything meant to keep its shape needs a `UIAspectRatioConstraint`.
4. Every `TextLabel` and `TextButton` should have `TextScaled` on with a
   `UITextSizeConstraint`.
5. Then run the device emulator on the smallest phone in the list.

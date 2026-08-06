---
title: "Why your button works in Studio but does nothing on mobile"
description: The button is fine. It is usually the input code filtering for a mouse, or something invisible sitting on top of it.
date: 2026-08-06
category: UI
kind: learn
level: Beginner
minutes: 8
---

The button works on your computer. On a phone, tapping it does nothing at all — no
error, no response.

There are four common causes. The first is by far the most frequent, and it is a
single line of code.

## 1. You are only listening for a mouse

If your input code checks the input type, and only accepts mouse buttons, touch
input never matches:

```lua
-- breaks on phones: a tap is not MouseButton1
UserInputService.InputBegan:Connect(function(input)
	if input.UserInputType == Enum.UserInputType.MouseButton1 then
		doTheThing()
	end
end)
```

Accept touch as well:

```lua
local UserInputService = game:GetService("UserInputService")

UserInputService.InputBegan:Connect(function(input, gameProcessed)
	if gameProcessed then
		return
	end

	if input.UserInputType == Enum.UserInputType.MouseButton1
		or input.UserInputType == Enum.UserInputType.Touch then
		doTheThing()
	end
end)
```

Note the `gameProcessed` check. Without it, this fires while the player is typing
in chat — which produces the opposite bug, where an action triggers when it should
not.

## 2. You are using the deprecated Mouse object

Older tutorials use `Player:GetMouse()`. Phones have no mouse. Anything built on
`mouse.Button1Down`, `mouse.Hit`, or `mouse.Target` has no touch equivalent and
simply never fires.

For a GUI button, the direct events are the right tool and they already handle
touch:

```lua
local button = script.Parent

button.Activated:Connect(function()
	doTheThing()
end)
```

`GuiButton.Activated` fires for mouse clicks, taps and gamepad activation, which is
usually what you actually meant. `MouseButton1Click` also fires on tap despite the
name, so existing code using it is not broken — but `Activated` states the intent
better and covers gamepad too.

For clicking objects in the world rather than a GUI, use a `ClickDetector` (its
`MouseClick` event fires on tap) or a `ProximityPrompt`, which was designed for
cross-platform interaction and gives you the button hint for free.

## 3. Something invisible is on top of it

This one produces the most confusing version of the symptom, because the button
looks completely normal.

A `Frame` with `BackgroundTransparency = 1` is invisible but still absorbs input.
If it overlaps your button and sits above it, taps hit the frame.

Two things to check:

```lua
-- a transparent frame that should not eat input
overlay.Active = false

-- and make sure the button is above it
button.ZIndex = 2
```

`Active = false` on a `Frame` lets input pass through to whatever is behind it.
This is the fix for the classic "invisible full-screen container swallowing
everything."

Why does it work with a mouse? Often it does not, and you never noticed, because
your cursor was landing on a part of the button the overlay did not cover. A thumb
is much bigger than a cursor.

> [!note]
> To find the culprit, temporarily set every `Frame`'s `BackgroundTransparency` to
> `0.5` and look at what is actually stacked over your button. It is usually
> obvious immediately.

## 4. The button is off-screen, or too small to hit

Covered in more depth in the Scale vs Offset guide, but the short version:

- A button positioned in **Offset** pixels can be entirely outside a smaller
  screen. It is not ignoring your tap; it is not there.
- A button under roughly 44 pixels on its shortest side is very hard to hit with a
  thumb, so it feels broken intermittently rather than completely.

```lua
button.Size = UDim2.new(0.4, 0, 0, 48)
button.AnchorPoint = Vector2.new(0.5, 0.5)
button.Position = UDim2.fromScale(0.5, 0.85)
```

## Testing it properly

Studio's device emulator (**Test** tab → **Device**) changes the viewport, so it
catches causes 3 and 4. It does **not** faithfully emulate touch, so it will not
reliably catch causes 1 and 2.

To catch those, check the code rather than the behaviour: search your LocalScripts
for `MouseButton1`, `GetMouse`, and `Button1Down`. Every hit is a place where touch
was probably not considered.

You can also check the platform at runtime, which is useful for showing different
hints:

```lua
local UserInputService = game:GetService("UserInputService")

if UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled then
	hintLabel.Text = "Tap to open"
else
	hintLabel.Text = "Press E to open"
end
```

Checking both flags matters: some devices report `TouchEnabled` **and** have a
keyboard, so testing touch alone will misclassify laptops with touchscreens.

<!-- OWN_EXPERIENCE -->

## The order to check things

1. Does the button's handler use `Activated` or `MouseButton1Click`? If it uses
   `UserInputService` with a type filter, that is your bug.
2. Any `GetMouse()` or `mouse.Hit` in the path? Rewrite that part.
3. Set all frames to 50% transparency and look for an overlay above the button.
4. Run the device emulator on the smallest phone and confirm the button is actually
   on screen and at least 44 pixels tall.

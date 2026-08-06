---
title: "A notification system: server-triggered toasts that stack"
description: One RemoteEvent, a queue, and a reusable template. Messages that appear, stack neatly, and clean themselves up.
date: 2026-08-06
category: UI
kind: recipe
level: Intermediate
minutes: 11
---

"You earned 50 coins." "Round starting." "Not enough Robux." Almost every game needs
short messages triggered from the server, and the naive version — one label that gets
overwritten — loses messages whenever two arrive close together.

## The setup

```text
ReplicatedStorage
└── Remotes
    └── Notify              (RemoteEvent)

StarterGui
└── Notifications           (ScreenGui)
    ├── Container           (Frame, with a UIListLayout)
    └── Template            (Frame, Visible = false)
        ├── Icon            (ImageLabel)
        └── Message         (TextLabel)
```

Put a `UIListLayout` in `Container` with `VerticalAlignment = Bottom` and
`SortOrder = LayoutOrder`. The layout does the stacking so you never compute positions.

## The client

```lua
-- StarterPlayerScripts/Notifications.client.lua
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local notify = ReplicatedStorage:WaitForChild("Remotes"):WaitForChild("Notify")

local player = Players.LocalPlayer
local gui = player:WaitForChild("PlayerGui"):WaitForChild("Notifications")
local container = gui:WaitForChild("Container")
local template = gui:WaitForChild("Template")

local MAX_VISIBLE = 4
local LIFETIME = 4
local FADE = 0.22

local STYLES = {
	info    = { colour = Color3.fromRGB(48, 54, 62),  accent = Color3.fromRGB(77, 159, 230) },
	success = { colour = Color3.fromRGB(34, 56, 42),  accent = Color3.fromRGB(120, 200, 120) },
	warning = { colour = Color3.fromRGB(62, 48, 34),  accent = Color3.fromRGB(224, 150, 70) },
	error   = { colour = Color3.fromRGB(64, 38, 38),  accent = Color3.fromRGB(232, 96, 96) },
}

local active = {}
local nextOrder = 0

local function dismiss(toast)
	if toast:GetAttribute("Dismissing") then
		return
	end
	toast:SetAttribute("Dismissing", true)

	local out = TweenService:Create(
		toast,
		TweenInfo.new(FADE, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
		{ BackgroundTransparency = 1, Position = UDim2.new(0.25, 0, 0, 0) }
	)

	out.Completed:Connect(function()
		for i, t in ipairs(active) do
			if t == toast then
				table.remove(active, i)
				break
			end
		end
		toast:Destroy()
	end)

	out:Play()
end

local function show(message, style)
	local look = STYLES[style] or STYLES.info

	local toast = template:Clone()
	nextOrder += 1
	toast.LayoutOrder = nextOrder
	toast.Name = "Toast"
	toast.BackgroundColor3 = look.colour
	toast.Message.Text = tostring(message)
	toast.Visible = true

	local stripe = toast:FindFirstChild("Accent")
	if stripe then
		stripe.BackgroundColor3 = look.accent
	end

	-- animate in
	toast.BackgroundTransparency = 1
	toast.Position = UDim2.new(0.25, 0, 0, 0)
	toast.Parent = container

	TweenService:Create(
		toast,
		TweenInfo.new(FADE, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
		{ BackgroundTransparency = 0.1, Position = UDim2.new(0, 0, 0, 0) }
	):Play()

	table.insert(active, toast)

	-- oldest out if we are over the cap
	while #active > MAX_VISIBLE do
		dismiss(active[1])
		table.remove(active, 1)
	end

	task.delay(LIFETIME, function()
		if toast.Parent then
			dismiss(toast)
		end
	end)
end

notify.OnClientEvent:Connect(show)
```

## The server

```lua
-- ServerScriptService/Notify.server.lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local notify = ReplicatedStorage.Remotes.Notify

local function notifyPlayer(player, message, style)
	notify:FireClient(player, message, style or "info")
end

local function notifyAll(message, style)
	notify:FireAllClients(message, style or "info")
end

-- usage
notifyPlayer(player, "You earned 50 coins", "success")
notifyAll("Round starting in 10 seconds", "info")
```

## The parts that matter

**`LayoutOrder` increments forever.** A `UIListLayout` sorts by it, so an
ever-increasing counter keeps new toasts in the right place without renumbering
anything. Reusing numbers, or relying on child order, produces toasts that jump around
as others expire.

**The `Dismissing` attribute guards double-dismissal.** A toast can be dismissed by the
lifetime timer and by the over-cap logic at nearly the same moment. Without the guard
you get two tweens and a `Destroy` on an already-destroyed instance.

**`toast.Parent` is checked inside `task.delay`.** Four seconds is a long time in UI
terms — the toast may already be gone, and touching a destroyed instance errors.

**`table.remove` in the completion handler.** Removing from `active` when the animation
finishes rather than when dismissal starts keeps the cap accurate while things are
fading out.

## Never trust the client to notify itself

The remote fires **server → client** only. There is no `OnServerEvent` handler here on
purpose.

If you add one so clients can trigger their own notifications, a player can spam
`FireServer` and — if you broadcast it — put arbitrary text on everyone's screen. Games
have shipped that bug. Keep the direction one-way.

## Deduplicating repeats

Ten coin pickups in two seconds should not be ten toasts:

```lua
local recent = {}
local DEDUPE_WINDOW = 1.5

local function show(message, style)
	local key = tostring(message)
	local now = os.clock()

	if recent[key] and now - recent[key] < DEDUPE_WINDOW then
		return
	end
	recent[key] = now

	-- ...rest as above
end
```

For counters specifically, it is better to accumulate on the server and send one
message — "You earned 250 coins" — than to dedupe identical strings on the client.

## Positioning

```lua
container.AnchorPoint = Vector2.new(1, 1)
container.Position = UDim2.new(1, -16, 1, -16)     -- bottom right
container.Size = UDim2.new(0, 300, 0, 400)
container.BackgroundTransparency = 1
```

Bottom-right is conventional on desktop. On phones, bottom-centre reads better and
avoids the thumb resting area on the right — worth branching on
`UserInputService.TouchEnabled`.

Set `container.Active = false` and `BackgroundTransparency = 1` so the invisible
container does not swallow taps meant for buttons behind it. That is a real bug and an
easy one to miss, because it only shows up on touch.

## Testing it

Fire ten at once from the Command Bar and watch what happens:

```lua
for i = 1, 10 do
	game.ReplicatedStorage.Remotes.Notify:FireAllClients("Message " .. i, "info")
end
```

You should see four, stacked, with the rest arriving as the earlier ones expire — and
no errors in the console as they overlap. That burst is the case the naive
single-label version fails, and it is the reason for the queue.

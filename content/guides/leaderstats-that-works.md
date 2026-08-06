---
title: "A leaderstats setup that shows the value you meant"
description: The exact folder name, the right value types, and why your stat shows 0 or nothing at all.
date: 2026-08-06
category: Data
kind: recipe
level: Beginner
minutes: 7
---

The player list on the right of the screen can show your own stats. It works by
convention, not configuration: Roblox looks for a folder with one exact name.

## The working version

```lua
-- ServerScriptService/Leaderstats.server.lua
local Players = game:GetService("Players")

Players.PlayerAdded:Connect(function(player)
	local stats = Instance.new("Folder")
	stats.Name = "leaderstats"        -- this exact name, lowercase
	stats.Parent = player

	local coins = Instance.new("IntValue")
	coins.Name = "Coins"
	coins.Value = 0
	coins.Parent = stats

	local level = Instance.new("IntValue")
	level.Name = "Level"
	level.Value = 1
	level.Parent = stats
end)
```

That is the whole feature. The column heading is the value's `Name`; the cell is its
`Value`.

## The five reasons it shows nothing

**The folder name is wrong.** It must be exactly `leaderstats` — lowercase, one word,
no space. `Leaderstats`, `LeaderStats` and `leaderStats` all produce a player list
with no columns and no error.

**It is parented to the character instead of the player.** The folder goes in the
`Player` object, not in their character model. The character is destroyed on death;
the player object is not.

**The script is a LocalScript.** Stats created on the client are visible to nobody,
including the player list. This must be a server `Script` in `ServerScriptService`.

**You are using the wrong value type.** Only these show up:

| Type | Holds |
|---|---|
| `IntValue` | whole numbers |
| `NumberValue` | decimals |
| `StringValue` | text |
| `BoolValue` | true/false |

An `ObjectValue`, a `Folder`, or a `Vector3Value` will not display.

**`PlayerAdded` fired before your script ran.** In Studio you are usually in the
server before the script starts, so your own stats never get created. See the fix
below.

## The PlayerAdded race

This bites in Studio almost every time and occasionally on a live server:

```lua
-- misses anyone who joined before this line ran
Players.PlayerAdded:Connect(setupStats)
```

Handle both cases:

```lua
local function setupStats(player)
	if player:FindFirstChild("leaderstats") then
		return                        -- already done
	end
	-- ...create the folder as above
end

Players.PlayerAdded:Connect(setupStats)

for _, player in ipairs(Players:GetPlayers()) do
	task.spawn(setupStats, player)    -- anyone already here
end
```

The `FindFirstChild` guard makes the function safe to call twice, which matters
because in a race both paths can fire.

## Only two or three columns fit

The default player list shows a limited number of stat columns — in practice two or
three before it starts truncating, and fewer on a phone.

Put the important one first (children are ordered by creation) and keep the rest in a
custom GUI. A leaderstats folder with eight values is a player list nobody can read.

## Changing values

Just set them. Replication is automatic:

```lua
local function addCoins(player, amount)
	local stats = player:FindFirstChild("leaderstats")
	if not stats then return end

	local coins = stats:FindFirstChild("Coins")
	if not coins then return end

	coins.Value += amount
end
```

Always on the server. A client can change its own local copy, but that change goes
nowhere — and if your server later reads that value expecting the client's number,
you have handed players a cheat.

> [!warning]
> Do not use leaderstats as your source of truth for currency. It is a display
> layer. Keep the authoritative number in a server-side table and mirror it into
> leaderstats for display. Otherwise every piece of code that touches money is
> reaching into a UI element.

## Reading it on the client

```lua
local Players = game:GetService("Players")
local player = Players.LocalPlayer

local stats = player:WaitForChild("leaderstats")
local coins = stats:WaitForChild("Coins")

local label = script.Parent:WaitForChild("CoinLabel")

local function redraw()
	label.Text = string.format("%d coins", coins.Value)
end

coins.Changed:Connect(redraw)
redraw()
```

`WaitForChild` on both, because the client may run before the server has created
them. The final `redraw()` sets the initial text — without it the label stays at
whatever you typed in Studio until the value first changes.

## Formatting big numbers

`IntValue` shows raw digits, so a million coins reads as `1000000`. The player list
cannot be formatted, but a `StringValue` can be:

```lua
local display = Instance.new("StringValue")
display.Name = "Coins"
display.Parent = stats

local function format(n)
	if n >= 1e9 then return string.format("%.1fB", n / 1e9) end
	if n >= 1e6 then return string.format("%.1fM", n / 1e6) end
	if n >= 1e3 then return string.format("%.1fK", n / 1e3) end
	return tostring(n)
end

-- keep the real number elsewhere; this one is only for display
display.Value = format(realCoins)
```

Note the trade-off: sorting by a `StringValue` sorts alphabetically, so `"9K"` sorts
above `"10K"`. If sorting matters, keep the `IntValue`.

## Checking it

1. Run the game and look in the Explorer under `Players > YourName`. Is there a
   folder called exactly `leaderstats`?
2. Open it. Are the children `IntValue`/`StringValue` and named as you expect?
3. If both are true and the list is still empty, you are looking at a client-created
   copy — confirm the script is a `Script` in `ServerScriptService`, not a
   `LocalScript`.

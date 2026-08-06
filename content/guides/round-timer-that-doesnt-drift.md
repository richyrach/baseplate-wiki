---
title: "Round-based games: a timer loop that doesn't drift"
description: Counting down with wait(1) loses seconds every round. Use a deadline instead, and the clock stays honest for hours.
date: 2026-08-06
category: Multiplayer
kind: recipe
level: Intermediate
minutes: 9
---

The obvious countdown is wrong in a way that only shows up after a while:

```lua
for i = 60, 0, -1 do
	timerValue.Value = i
	task.wait(1)
end
```

`task.wait(1)` does not wait exactly one second. It waits *at least* one second and
returns on the next frame after that. On a busy server that might be 1.02 seconds.
Sixty iterations of a small overshoot is a round that runs a second or two long, and
after twenty rounds your timer and the actual clock have visibly parted company.

The fix is to stop counting elapsed waits and start comparing against a deadline.

## The pattern

```lua
local function countdown(seconds, onTick)
	local deadline = os.clock() + seconds
	local lastShown = nil

	while true do
		local remaining = deadline - os.clock()
		if remaining <= 0 then
			break
		end

		local whole = math.ceil(remaining)
		if whole ~= lastShown then
			lastShown = whole
			onTick(whole)
		end

		task.wait(0.1)
	end

	onTick(0)
end
```

The deadline is computed once. Every iteration asks "how much is left?" rather than
"how much have I counted?", so a slow frame cannot accumulate error — the next
iteration simply reports a slightly smaller number.

Polling at 0.1s and only firing `onTick` when the whole second changes means the
display is accurate to a tenth of a second without sending ten updates a second to
anyone.

## A full round loop

```lua
-- ServerScriptService/RoundManager.server.lua
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local state = Instance.new("Folder")
state.Name = "RoundState"
state.Parent = ReplicatedStorage

local phase = Instance.new("StringValue")
phase.Name = "Phase"
phase.Value = "Waiting"
phase.Parent = state

local clockValue = Instance.new("IntValue")
clockValue.Name = "Clock"
clockValue.Parent = state

local MIN_PLAYERS = 2
local INTERMISSION = 15
local ROUND_LENGTH = 120

local function setPhase(name)
	phase.Value = name
end

local function enoughPlayers()
	return #Players:GetPlayers() >= MIN_PLAYERS
end

local function runRound()
	setPhase("Playing")
	-- start-of-round work goes here: teleport, assign teams, reset scores

	countdown(ROUND_LENGTH, function(remaining)
		clockValue.Value = remaining
	end)

	setPhase("Ended")
	task.wait(3)
end

task.spawn(function()
	while true do
		setPhase("Waiting")
		clockValue.Value = 0

		while not enoughPlayers() do
			task.wait(1)
		end

		setPhase("Intermission")
		countdown(INTERMISSION, function(remaining)
			clockValue.Value = remaining
		end)

		if enoughPlayers() then
			runRound()
		end
	end
end)
```

Two details worth noticing:

**The player check happens twice.** Once to leave the waiting phase, and again after
the intermission — because someone may have left during those fifteen seconds.
Without the second check you start a one-player round.

**Phase and clock are `Value` objects in `ReplicatedStorage`**, not RemoteEvents.
Value objects replicate automatically and the client can read them at any time,
including a player who joins mid-round. With RemoteEvents, a late joiner sees
nothing until the next event fires.

## The client side

```lua
-- StarterPlayerScripts/RoundHud.client.lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local state = ReplicatedStorage:WaitForChild("RoundState")
local phase = state:WaitForChild("Phase")
local clockValue = state:WaitForChild("Clock")

local label = script.Parent:WaitForChild("TimerLabel")

local function format(seconds)
	return string.format("%d:%02d", seconds // 60, seconds % 60)
end

local function redraw()
	if phase.Value == "Waiting" then
		label.Text = "Waiting for players"
	elseif phase.Value == "Intermission" then
		label.Text = "Next round in " .. format(clockValue.Value)
	elseif phase.Value == "Playing" then
		label.Text = format(clockValue.Value)
	else
		label.Text = "Round over"
	end
end

phase.Changed:Connect(redraw)
clockValue.Changed:Connect(redraw)
redraw()
```

The final `redraw()` call handles the join case — without it the label stays blank
until the next change fires.

## os.clock, not tick

`tick()` is deprecated. For measuring elapsed time on one machine, `os.clock()` is
the right call and it is monotonic, so it cannot jump if the system clock changes.

If you need a timestamp the client and server agree on, use
`workspace:GetServerTimeNow()` on both sides. Sending a *deadline* rather than a
*remaining count* lets each client run its own smooth countdown with no further
network traffic:

```lua
-- server, once per round
deadlineValue.Value = workspace:GetServerTimeNow() + ROUND_LENGTH

-- client, every frame if you want a smooth bar
local remaining = deadlineValue.Value - workspace:GetServerTimeNow()
```

That is the approach to reach for if you want a millisecond-smooth progress bar.

> [!warning]
> Never drive round logic from the client's countdown. The client's clock is under
> the player's control. The server owns when the round ends; the client only
> displays it.

## Interrupting a round early

A team wiping out should not require waiting for the clock. Add a signal the
countdown can watch:

```lua
local roundOver = Instance.new("BindableEvent")
local finished = false

roundOver.Event:Connect(function()
	finished = true
end)

local deadline = os.clock() + ROUND_LENGTH
while os.clock() < deadline and not finished do
	clockValue.Value = math.ceil(deadline - os.clock())
	task.wait(0.1)
end
```

Because the loop checks a flag rather than sleeping through the whole duration, it
can exit within a tenth of a second of the condition being met.

<!-- OWN_EXPERIENCE -->

## Verifying it does not drift

Print the real duration at the end of each round:

```lua
local started = os.clock()
runRound()
print(string.format("round took %.2fs (expected %d)", os.clock() - started, ROUND_LENGTH))
```

Leave it running for ten rounds. With the deadline pattern the number stays within a
fraction of a second every time. With the `wait(1)` loop, watch it grow.

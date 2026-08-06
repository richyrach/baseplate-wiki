---
title: "Why your game lags with 20 players when it was fine with 2"
description: Most Roblox performance problems scale with player count for one of five reasons. How to find which one you have instead of guessing.
date: 2026-08-06
category: Performance
kind: learn
level: Intermediate
minutes: 12
---

Two players: smooth. Twenty players: unplayable.

Something in your game costs per-player, and twenty is ten times two. The useful move
is to find out *which* thing rather than optimising at random — and Roblox gives you
the numbers to find out.

## First: is it the server or the client?

These have completely different causes, and the answer takes ten seconds.

Press `F9`, or `Shift+F5` for the performance stats overlay, and look at:

- **Server frame time / heartbeat** — how long the server takes per tick. Should sit
  near 16ms. Climbing means the server is the bottleneck.
- **Client frame time** — the same, on your machine.
- **Ping** — network latency.

Then:

- **Server high, client fine** → server-side logic. Causes 1, 2, 3 below.
- **Client high, server fine** → rendering or client scripts. Causes 4, 5.
- **Both fine but it feels bad** → network. Cause 3.

Guessing without this split wastes hours. A rendering fix will do nothing for a
server-bound game.

## 1. Per-player loops

Something running per player per frame is 10x the work at 20 players:

```lua
-- 20 players x 60 fps = 1200 executions a second
RunService.Heartbeat:Connect(function()
	for _, player in ipairs(Players:GetPlayers()) do
		local character = player.Character
		if character then
			checkZone(character)      -- and this loops over 50 zones...
		end
	end
end)
```

Twenty players against fifty zones every frame is 60,000 checks a second.

Two fixes, and they compose:

**Run it less often.** Zone checks do not need 60Hz:

```lua
task.spawn(function()
	while task.wait(0.25) do
		for _, player in ipairs(Players:GetPlayers()) do
			local character = player.Character
			if character then
				checkZone(character)
			end
		end
	end
end)
```

Four times a second instead of sixty. For zone detection nobody can tell.

**Use the engine's spatial queries instead of your own loop.** `Region3` scanning by
hand is slow; `GetPartBoundsInBox` is implemented in C++:

```lua
local parts = workspace:GetPartBoundsInBox(zone.CFrame, zone.Size)
```

Better still, `Touched`/`TouchEnded` on a zone part is event-driven and costs nothing
when nobody moves.

## 2. Connections that are never disconnected

This is the one that produces the distinctive symptom of a server getting slower the
longer it stays up, rather than being slow immediately.

```lua
-- a new connection every respawn, and the old one still runs
Players.PlayerAdded:Connect(function(player)
	player.CharacterAdded:Connect(function(character)
		RunService.Heartbeat:Connect(function()
			track(character)
		end)
	end)
end)
```

After ten respawns that player has ten `Heartbeat` connections, nine of them
tracking destroyed characters.

Keep the connection and clean it up:

```lua
Players.PlayerAdded:Connect(function(player)
	player.CharacterAdded:Connect(function(character)
		local connection
		connection = RunService.Heartbeat:Connect(function()
			if not character.Parent then
				connection:Disconnect()
				return
			end
			track(character)
		end)
	end)
end)
```

To confirm you have this problem, watch **Memory** in the Developer Console over
fifteen minutes on a populated server. A number that only ever climbs is a leak.

## 3. RemoteEvent traffic

Every RemoteEvent call is network traffic, and `FireAllClients` multiplies by player
count.

```lua
-- 60 fps x 20 players = 1200 messages a second
RunService.Heartbeat:Connect(function()
	updatePosition:FireAllClients(vehicle.Position)
end)
```

Three fixes:

**Send less often.** Most state does not need 60Hz. 10Hz is plenty for a scoreboard.

**Send to who needs it.** `FireClient(player, ...)` beats `FireAllClients` when only
one player cares.

**Use replicated properties instead of events.** A `Value` object, or an attribute,
replicates automatically and is not something you can accidentally spam:

```lua
scoreValue.Value = newScore     -- replicates once, to everyone, automatically
```

Check the **Network** tab in the Developer Console to see what is actually being
sent. It is usually surprising.

## 4. Part count and unanchored parts

Client-side frame time is often just rendering too much.

- **Unanchored parts** are simulated every frame. Anchor everything static. This is
  frequently the single biggest win available.
- **Total part count.** Thousands of individual parts is expensive; unions and meshes
  render far more cheaply than the parts they replace.
- **Transparent and reflective surfaces** cost more than opaque ones.
- **Particle emitters** are expensive per particle. Twenty players with a trail each
  is a lot of particles.

The audit:

```lua
local total, unanchored = 0, 0
for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("BasePart") then
		total += 1
		if not d.Anchored then
			unanchored += 1
		end
	end
end
print(string.format("%d parts, %d unanchored (%.0f%%)",
	total, unanchored, unanchored / total * 100))
```

If a meaningful share of a static map is unanchored, fix that before anything else.

## 5. Characters are expensive

Each character is roughly 15 parts plus a `Humanoid`, and `Humanoid` is one of the
most expensive objects in the engine — it does state machines, physics and animation
every frame.

Twenty players is 300 parts and 20 Humanoids that all have to be simulated and
rendered by every client.

You cannot avoid player characters, but you can avoid *extra* Humanoids. NPCs are
often the real cost:

```lua
-- an NPC that does not need to walk does not need a Humanoid
npc.Humanoid:Destroy()
```

If the NPC is purely decorative, removing the `Humanoid` removes most of its cost.
If it needs to move, `Humanoid.WalkSpeed = 0` does not help — the state machine still
runs.

## Measure, then fix

The MicroProfiler (`Ctrl+F6`) shows where frame time actually goes. It looks
intimidating and you only need one skill: find the widest bar and read its label.
That label is your bottleneck. Fix it, measure again.

Optimising the second-widest bar has no measurable effect, which is why "I optimised
loads of things and it is still slow" is such a common outcome.

> [!warning]
> Do not optimise from a two-player Studio test. Several of these problems only
> appear with real player counts, and two of them — connection leaks and memory
> growth — only appear over time. Test in a live server with people in it.

<!-- OWN_EXPERIENCE -->

## The order to work in

1. `Shift+F5` and split server versus client. Do not skip this.
2. Anchor everything static. Cheap, big, no downside.
3. Count your `Heartbeat` and `RenderStepped` connections. Every one should have a
   disconnect path.
4. Move per-frame loops to a slower timer, or to events.
5. Check the Network tab for RemoteEvent spam.
6. Watch Memory over fifteen minutes for a leak.
7. Only now open the MicroProfiler, and only fix the widest bar.

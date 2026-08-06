---
title: "Why your custom animation only plays for you"
description: Animation permissions, the Animator object, and which side has to play a track for everyone to see it.
date: 2026-08-06
category: Animation
kind: learn
level: Intermediate
minutes: 10
---

You upload an animation, play it, and it looks right on your screen. Someone else in
the server sees your character standing still.

Or worse: it works for you in Studio and fails for everyone including you once
published.

There are three distinct causes and they have different symptoms, so identifying
which one you have is most of the work.

## 1. The animation is not owned by whoever owns the game

This is the most common cause, and it is not a code problem at all.

An animation asset belongs to the account that uploaded it. A game can only play
animations owned by the same account or group that owns the **game**.

So:

- You upload an animation to your account, and the game is under your account →
  works.
- You upload to your account, then move the game into a group → **stops working.**
- A friend uploads it and you use the ID → does not work.
- You took the ID from a free model or a tutorial → almost certainly does not work.

The symptom is distinctive: it fails for everyone, consistently, and the output
usually carries a message about the animation failing to load or not being owned by
the game creator.

The fix is to re-upload the animation under the account or group that owns the game.
There is no scripting workaround — it is a deliberate permission rule.

> [!note]
> This is the single most likely reason a "working" animation breaks the day you
> move a game into a group. If a working animation stops working and you changed
> nothing in the code, check ownership first.

## 2. You are using the deprecated LoadAnimation

`Humanoid:LoadAnimation()` is deprecated. The current path is the `Animator` object
that lives inside the `Humanoid`:

```lua
local character = player.Character or player.CharacterAdded:Wait()
local humanoid = character:WaitForChild("Humanoid")
local animator = humanoid:WaitForChild("Animator")

local animation = Instance.new("Animation")
animation.AnimationId = "rbxassetid://YOUR_ID_HERE"

local track = animator:LoadAnimation(animation)
track:Play()
```

Deprecated functions still work for a while, so this rarely causes an immediate
failure — but it does produce warnings, and it is the kind of thing that eventually
stops working without notice.

Note `WaitForChild("Animator")`. The `Animator` is created by the engine and may not
exist the instant a character spawns. Indexing it directly is a race, and it is a
common cause of intermittent failures.

## 3. It is being played on the wrong side

This is the one that produces "only I can see it."

The rules, as they behave in practice:

- An animation played on the **server**, through the character's `Animator`,
  replicates to everyone.
- An animation played on the **client**, on that client's **own** character,
  replicates to everyone. Roblox replicates the local player's own animations
  outward, which is why local input handling works.
- An animation played on the **client**, on **someone else's** character or on an
  arbitrary rig, does **not** replicate. Only that client sees it.

That third case is the bug. Code like this, in a LocalScript, looks reasonable and is
visible only to the person running it:

```lua
-- LocalScript: only this client sees the NPC wave
local npc = workspace.Shopkeeper
local animator = npc.Humanoid.Animator
animator:LoadAnimation(waveAnimation):Play()
```

For an NPC or any rig that is not the local player's character, play it on the
server:

```lua
-- ServerScriptService
local npc = workspace:WaitForChild("Shopkeeper")
local animator = npc:WaitForChild("Humanoid"):WaitForChild("Animator")

local track = animator:LoadAnimation(waveAnimation)
track:Play()
```

For the local player's own actions, playing on the client is correct and preferable —
it is instant, with no round trip.

## Nothing plays at all: priority

If a track loads without error and simply has no visible effect, it is usually being
overridden by the default animation script, which is constantly playing idle, walk
and run tracks.

```lua
track.Priority = Enum.AnimationPriority.Action
track:Play()
```

The order, lowest to highest: `Core`, `Idle`, `Movement`, `Action`, `Action2`,
`Action3`, `Action4`.

The default character animations run at `Movement` and `Idle`. Anything you want to
see over walking needs to be at least `Action`.

You can also set the priority on the animation itself in the Animation Editor, which
is usually the better place — then every script that plays it gets it right.

## Blending and stopping

```lua
track:Play(0.2)                      -- fade in over 0.2s
track:Stop(0.3)                      -- fade out over 0.3s
track:AdjustSpeed(1.5)               -- 1.5x speed
track.Looped = true
```

The fade arguments are what separate an animation that snaps in jarringly from one
that reads as smooth. A short fade, around 0.1 to 0.3 seconds, is almost always an
improvement.

Keep a reference to the track so you can stop it. Losing the reference means the
animation cannot be stopped except by playing something at higher priority.

```lua
local tracks = {}

local function playOnce(name, animation)
	if tracks[name] then
		tracks[name]:Stop(0.1)
	end
	local track = animator:LoadAnimation(animation)
	track.Priority = Enum.AnimationPriority.Action
	track:Play(0.1)
	tracks[name] = track
	return track
end
```

## R6 versus R15

An animation authored for an R15 rig will not play correctly on an R6 character and
vice versa — the joint names differ, so the animation targets bones that do not
exist.

Check **Game Settings → Avatar → Animation** for which rig type your game uses, and
author animations against the same one. A "nothing happens, no errors" symptom on a
correctly-owned animation is often this.

## Diagnosis in order

1. **Does anyone see it, including you?** No → ownership (cause 1). Check who
   uploaded the asset and who owns the game.
2. **Do only you see it?** → wrong side (cause 3). Move the play call to the server
   if it is not your own character.
3. **Does the track load with no error but nothing moves?** → priority, or an R6/R15
   mismatch.
4. **Does it work sometimes?** → you are indexing `Animator` before it exists. Use
   `WaitForChild`.
5. Check the Developer Console (`F9`) on **both** the client and server tabs. Asset
   loading failures are reported, and they name the reason.

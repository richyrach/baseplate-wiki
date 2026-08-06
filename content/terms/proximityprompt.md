---
term: ProximityPrompt
category: Scripting
summary: The cross-platform way to make a world object interactive. Handles keyboard, gamepad and touch with no extra code.
---

A `ProximityPrompt` parented to a part gives players a prompt when they get close, and
fires `Triggered` on the server when they act on it.

```lua
local prompt = Instance.new("ProximityPrompt")
prompt.ActionText = "Open"
prompt.ObjectText = "Door"
prompt.KeyboardKeyCode = Enum.KeyCode.E
prompt.MaxActivationDistance = 10
prompt.RequiresLineOfSight = false
prompt.HoldDuration = 0
prompt.Parent = door

prompt.Triggered:Connect(function(player)
	openDoor(player)
end)
```

## Why prefer it over ClickDetector

- **Cross-platform for free.** Keyboard shows the key, gamepad shows a button, touch
  shows a tappable circle. A `ClickDetector` needs you to think about touch yourself.
- **It advertises itself.** `ActionText` tells the player the object is interactive,
  which a click detector does not.
- **Distance is enforced by the engine**, so a player cannot trigger it from across the
  map. That is one validation check you get without writing it.
- **`Triggered` provides the player**, already trusted, the same way `OnServerEvent`
  does.

## The properties that matter

| Property | Note |
|---|---|
| `ActionText` | the verb: "Open", "Buy", "Sit" |
| `ObjectText` | the noun, shown smaller |
| `MaxActivationDistance` | studs; enforced |
| `RequiresLineOfSight` | **defaults to `true`** |
| `HoldDuration` | seconds to hold; `0` is instant |
| `Enabled` | turn the prompt off without destroying it |
| `Exclusivity` | how it competes with nearby prompts |

`RequiresLineOfSight` defaulting to `true` is the most common surprise. A prompt that
vanishes when a decorative railing is between the player and the object is almost
always this.

`HoldDuration` of around `0.5` is worth setting for anything expensive or destructive —
a purchase, deleting a build — so a mistimed keypress does not commit.

## The events

```lua
prompt.Triggered:Connect(function(player) end)        -- completed
prompt.TriggerEnded:Connect(function(player) end)     -- released early
prompt.PromptShown:Connect(function() end)            -- client-side
prompt.PromptHidden:Connect(function() end)           -- client-side
```

`Triggered` fires on the server and is the one to build on. `PromptShown` and
`PromptHidden` fire on the client and are for local effects — a highlight, a sound.

## Still validate everything else

The engine guarantees the player was in range. It guarantees nothing else:

```lua
prompt.Triggered:Connect(function(player)
	local character = player.Character
	if not character then return end

	local humanoid = character:FindFirstChildOfClass("Humanoid")
	if not humanoid or humanoid.Health <= 0 then
		return                    -- dead players should not be shopping
	end

	if not hasEnoughCoins(player, PRICE) then
		return
	end

	grant(player)
end)
```

Rate limiting is worth adding too. `HoldDuration = 0` with a key held down can fire
repeatedly.

## One prompt, many players

A `ProximityPrompt` is a single instance shared by everyone in the server. You cannot
show different `ActionText` to different players from a server script.

If you need per-player text — "Buy" versus "Owned" — create the prompt from a
LocalScript so each client has its own, and keep a server-side handler for anything
that changes state.

## Styling it

Set `Style` to `Enum.ProximityPromptStyle.Custom` and the default UI is suppressed, so
you can draw your own from `PromptShown` and `PromptHidden` on the client. Worth doing
for a game with a strong visual identity; unnecessary otherwise, since the default
prompt is clear and already familiar to players.

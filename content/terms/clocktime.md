---
term: ClockTime
aka: TimeOfDay
category: Building
summary: The hour of the in-game day, 0 to 24, on Lighting. Drives the sun and moon.
---

`Lighting.ClockTime` is the in-game hour as a number from 0 to 24.

```lua
local Lighting = game:GetService("Lighting")

Lighting.ClockTime = 14        -- 2pm
Lighting.ClockTime = 0         -- midnight
```

`6` is roughly dawn, `12` noon, `18` dusk. Values outside 0–24 wrap, so `% 24` on
anything you compute is a good habit.

## The three ways to say the same thing

| Property / method | Form |
|---|---|
| `ClockTime` | number, `14.5` |
| `TimeOfDay` | string, `"14:30:00"` |
| `SetMinutesAfterMidnight(n)` | minutes, `870` |
| `GetMinutesAfterMidnight()` | minutes |

They are views onto the same underlying value. Setting one updates the others.

## The replication quirk

`ClockTime` is documented as **Not Replicated**, which reads like it cannot be driven
from the server. In practice setting it server-side does update every client, because
it writes through to `TimeOfDay`, which is replicated.

Because that is a documented-behaviour-versus-observed-behaviour gap, verify it in your
own game with **two clients** from the Test tab before shipping a cycle built on it. If
you see clients drift apart, set `TimeOfDay` instead.

Either way, run the cycle on the **server**. A client-side loop gives every player
their own private time of day.

## Frame-rate independent advancement

```lua
local DAY_LENGTH = 20 * 60           -- real seconds for a full cycle
local hoursPerSecond = 24 / DAY_LENGTH

while true do
	local dt = task.wait()
	Lighting.ClockTime = (Lighting.ClockTime + hoursPerSecond * dt) % 24
end
```

Multiplying by `dt` is what keeps the day the same length regardless of server load.
The common alternative — `ClockTime += 0.01` with a fixed `task.wait(0.1)` — runs at
whatever rate the server happens to tick.

## ClockTime alone looks flat

Moving the sun gives you a dark blue night and nothing else. The look comes from moving
the other `Lighting` properties in step: `Ambient`, `OutdoorAmbient`, `Brightness`,
`FogColor`, `FogEnd`, `ColorShift_Top`, `ExposureCompensation`.

Interpolating between a handful of keyframed values with `Color3:Lerp` gets you a
convincing dawn and dusk for about forty lines of code.

## GeographicLatitude

`Lighting.GeographicLatitude` changes the angle the sun travels across the sky. Higher
values give a lower, more raking sun — useful for a specific mood, and easy to forget
about when wondering why noon shadows look wrong.

## Watching for changes

```lua
Lighting:GetPropertyChangedSignal("ClockTime"):Connect(function()
	-- fires every frame while a cycle is running
end)
```

Guard anything expensive behind a check that the *visible* result actually changed — a
clock UI should only rebuild its text when the displayed minute rolls over, not sixty
times a second.

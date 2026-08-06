---
title: "Teams and spawns without players landing on top of each other"
description: Setting up Teams, tying spawn points to them, and spreading players out so nobody spawns inside someone else.
date: 2026-08-06
category: Multiplayer
kind: recipe
level: Beginner
minutes: 8
---

Two problems that arrive together: putting players on teams, and stopping everyone
from materialising in the same square metre.

## Creating the teams

Teams go in the `Teams` service. Add it from the Explorer's `+` if it is not there,
then:

```lua
-- ServerScriptService/TeamSetup.server.lua
local Teams = game:GetService("Teams")

local function makeTeam(name, colourName)
	local team = Instance.new("Team")
	team.Name = name
	team.TeamColor = BrickColor.new(colourName)
	team.AutoAssignable = false     -- we assign manually
	team.Parent = Teams
	return team
end

local runners = makeTeam("Runners", "Bright blue")
local seekers = makeTeam("Seekers", "Bright red")
```

`TeamColor` is a `BrickColor`, not a `Color3`, and it is the actual identity of the
team as far as spawn points are concerned. **Two teams must never share a
TeamColor** — Roblox matches spawns to teams by colour, so duplicates make spawning
unpredictable.

`AutoAssignable = false` stops Roblox putting joining players on a team by itself,
which you want if your round system decides team membership.

## Assigning players

```lua
local Players = game:GetService("Players")

local function assignBalanced(player)
	local counts = {}
	for _, team in ipairs(Teams:GetTeams()) do
		counts[team] = #team:GetPlayers()
	end

	local smallest, smallestCount = nil, math.huge
	for team, count in pairs(counts) do
		if count < smallestCount then
			smallest, smallestCount = team, count
		end
	end

	player.Team = smallest
end

Players.PlayerAdded:Connect(assignBalanced)
```

Setting `player.Team` is enough — `player.TeamColor` follows automatically. Setting
`TeamColor` directly also works but is the older style and easier to get wrong.

To respawn a player immediately after a team change, so they appear at their new
team's spawn:

```lua
player.Team = seekers
player:LoadCharacter()
```

Without `LoadCharacter`, they stay where they are until they next die.

## Tying spawn points to teams

For each `SpawnLocation`:

```lua
spawn.TeamColor = BrickColor.new("Bright blue")
spawn.Neutral = false                 -- only this team may use it
spawn.AllowTeamChangeOnTouch = false  -- touching it does not switch teams
```

Three properties, and each one is a distinct bug if you get it wrong:

- **`Neutral = true`** means anyone can spawn there, regardless of `TeamColor`. This
  is the default, and it is why "I set the TeamColor but everyone still spawns
  everywhere" happens. You must set `Neutral = false`.
- **`AllowTeamChangeOnTouch = true`** switches a player's team when they walk over
  the pad. Occasionally desirable, usually a surprise — players wander onto an enemy
  spawn and defect.
- **`Enabled = false`** takes a spawn out of use entirely, which is handy for
  disabling a base between rounds.

## Spreading players out

Roblox already spreads spawning across the available `SpawnLocation`s, so the real
fix for pile-ups is usually **more spawn pads**. Six pads per team beats one pad and
clever code.

When you need exact control, place characters yourself:

```lua
local function spawnPositionsAround(centre, count, radius)
	local positions = {}
	for i = 1, count do
		local angle = (i / count) * math.pi * 2
		positions[i] = centre + Vector3.new(
			math.cos(angle) * radius,
			0,
			math.sin(angle) * radius
		)
	end
	return positions
end

local function placeTeam(team, centre)
	local members = team:GetPlayers()
	local spots = spawnPositionsAround(centre, #members, 12)

	for i, player in ipairs(members) do
		local character = player.Character
		if character and character.PrimaryPart then
			character:PivotTo(CFrame.new(spots[i] + Vector3.new(0, 4, 0)))
		end
	end
end
```

Distributing points around a circle guarantees even spacing regardless of how many
players there are, which a random scatter does not.

Note `character:PivotTo(...)` rather than setting `HumanoidRootPart.CFrame`
directly. A character is a model of welded and jointed parts; moving the model moves
all of it, while moving one part can leave limbs behind.

The `+ Vector3.new(0, 4, 0)` matters too — placing a character exactly at floor
level lands it inside the floor, and the physics engine resolves that by launching
it.

## Team-aware behaviour elsewhere

Once teams exist, most gameplay code needs to check them:

```lua
local function sameTeam(playerA, playerB)
	return playerA.Team ~= nil and playerA.Team == playerB.Team
end
```

Use this before applying damage, or friendly fire will quietly be on. The `nil`
check matters — two players both on no team are not teammates, and without it they
would compare equal.

To react to changes:

```lua
player:GetPropertyChangedSignal("Team"):Connect(function()
	print(player.Name, "is now on", player.Team and player.Team.Name or "no team")
end)
```

> [!note]
> The default leaderboard groups players by team automatically once Teams exist.
> If you do not want that grouping, you need a custom player list rather than a
> Teams setting.

## Checklist

1. Every team has a **unique** `TeamColor`.
2. Every team spawn has `Neutral = false` and the matching `TeamColor`.
3. `AllowTeamChangeOnTouch` is `false` unless you specifically want defection.
4. At least four to six spawn pads per team.
5. Damage code checks `sameTeam` before applying.
6. Test with two clients and switch one team mid-round — confirm they respawn in the
   right base.

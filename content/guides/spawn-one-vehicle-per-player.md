---
title: "Spawning one vehicle per player and cleaning up the old one"
description: A server-side spawner that gives each player exactly one vehicle, removes their previous one, and cannot be abused to flood the server.
date: 2026-08-06
category: Vehicles
kind: recipe
level: Intermediate
minutes: 10
---

The requirement: a player picks a car, it appears at a spawn point, and their
previous one disappears. Nobody can fill the map with cars by clicking fast.

This has to live on the server. A client-spawned vehicle exists only for that
player, and letting the client decide how many to spawn is how you end up with a
server holding four hundred cars.

## Setup

```text
ServerStorage
└── Vehicles
    ├── Hatchback
    └── Pickup

ReplicatedStorage
└── Remotes
    └── RequestVehicle

Workspace
├── VehicleSpawns        (parts, one per spawn point)
└── SpawnedVehicles      (empty folder)
```

Vehicles live in `ServerStorage` so clients cannot read or clone them. Spawned ones
go in their own folder so cleanup never has to guess what is a vehicle.

## The spawner

```lua
-- ServerScriptService/VehicleSpawner.server.lua
local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local templates = ServerStorage:WaitForChild("Vehicles")
local spawnPoints = workspace:WaitForChild("VehicleSpawns")
local spawnedFolder = workspace:WaitForChild("SpawnedVehicles")
local requestVehicle = ReplicatedStorage.Remotes:WaitForChild("RequestVehicle")

local COOLDOWN = 3

local ownedVehicle = {}   -- [userId] = model
local lastRequest = {}    -- [userId] = os.clock()

local function despawn(userId)
	local existing = ownedVehicle[userId]
	if existing and existing.Parent then
		existing:Destroy()
	end
	ownedVehicle[userId] = nil
end

local function freeSpawnPoint()
	local points = spawnPoints:GetChildren()

	for i = #points, 2, -1 do          -- Fisher-Yates shuffle
		local j = math.random(i)
		points[i], points[j] = points[j], points[i]
	end

	for _, point in ipairs(points) do
		local region = workspace:GetPartBoundsInBox(
			point.CFrame + Vector3.new(0, 4, 0),
			Vector3.new(14, 8, 24)
		)

		local blocked = false
		for _, hit in ipairs(region) do
			if hit:IsDescendantOf(spawnedFolder) then
				blocked = true
				break
			end
		end

		if not blocked then
			return point
		end
	end

	return points[1]   -- everywhere is busy; reuse the first
end

local function spawnVehicle(player, vehicleName)
	local userId = player.UserId

	-- the client sends a name; the server decides if it is real
	if typeof(vehicleName) ~= "string" then
		return
	end

	local template = templates:FindFirstChild(vehicleName)
	if not template or not template:IsA("Model") then
		return
	end

	local now = os.clock()
	if lastRequest[userId] and now - lastRequest[userId] < COOLDOWN then
		return
	end
	lastRequest[userId] = now

	despawn(userId)

	local point = freeSpawnPoint()
	if not point then
		return
	end

	local vehicle = template:Clone()
	vehicle:SetAttribute("OwnerUserId", userId)

	-- pivot so the vehicle sits above the pad, not inside it
	local _, size = vehicle:GetBoundingBox()
	vehicle:PivotTo(point.CFrame * CFrame.new(0, size.Y / 2 + 1, 0))
	vehicle.Parent = spawnedFolder

	ownedVehicle[userId] = vehicle
	return vehicle
end

requestVehicle.OnServerEvent:Connect(spawnVehicle)

Players.PlayerRemoving:Connect(function(player)
	despawn(player.UserId)
	lastRequest[player.UserId] = nil
end)
```

## The four things that make it safe

**The client sends a name, never a model.** `FindFirstChild` against
`ServerStorage.Vehicles` means only vehicles you actually shipped can spawn. If the
client could send an instance, it could send anything.

**One vehicle per player, enforced by `despawn` before every spawn.** The count
cannot grow no matter how the request arrives.

**A cooldown.** `OnServerEvent` can be fired as fast as an exploiter likes. Without
the timer, a spawn loop is a denial-of-service on your own server.

**Cleanup on leave.** `PlayerRemoving` removes the vehicle and the cooldown entry,
so neither table grows forever.

## The client side

```lua
-- StarterPlayerScripts/VehicleMenu.client.lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local requestVehicle = ReplicatedStorage:WaitForChild("Remotes")
	:WaitForChild("RequestVehicle")

local button = script.Parent:WaitForChild("SpawnHatchback")

button.Activated:Connect(function()
	button.Active = false
	requestVehicle:FireServer("Hatchback")
	task.wait(3)
	button.Active = true
end)
```

The client-side disable is courtesy, not security — it stops honest players
double-clicking. The server cooldown is what actually protects you.

## Seating the driver

```lua
local function seatPlayer(player, vehicle)
	local seat = vehicle:FindFirstChildWhichIsA("VehicleSeat", true)
	local character = player.Character
	if not seat or not character then
		return
	end

	local humanoid = character:FindFirstChildOfClass("Humanoid")
	if humanoid then
		seat:Sit(humanoid)
	end
end
```

Call it right after `vehicle.Parent = spawnedFolder`. `Seat:Sit(humanoid)` is the
supported way — teleporting the character on top of the seat and hoping is not.

## Restricting the driver's seat to the owner

The `OwnerUserId` attribute set during spawn makes this easy:

```lua
local function guardSeat(vehicle)
	local seat = vehicle:FindFirstChildWhichIsA("VehicleSeat", true)
	if not seat then return end

	seat:GetPropertyChangedSignal("Occupant"):Connect(function()
		local occupant = seat.Occupant
		if not occupant then return end

		local player = Players:GetPlayerFromCharacter(occupant.Parent)
		if player and player.UserId ~= vehicle:GetAttribute("OwnerUserId") then
			seat:Sit(nil)   -- eject
		end
	end)
end
```

Whether you want this depends on the game — in a racing game, yes; in a sandbox,
letting friends drive each other's cars is the fun part.

## Idle cleanup

Vehicles left behind by players who are still online accumulate. A sweeper keeps
the map clear:

```lua
local IDLE_LIMIT = 300

task.spawn(function()
	while task.wait(30) do
		for _, vehicle in ipairs(spawnedFolder:GetChildren()) do
			local root = vehicle.PrimaryPart
			if root then
				local moving = root.AssemblyLinearVelocity.Magnitude > 1
				local since = vehicle:GetAttribute("IdleSince")

				if moving then
					vehicle:SetAttribute("IdleSince", nil)
				elseif not since then
					vehicle:SetAttribute("IdleSince", os.clock())
				elseif os.clock() - since > IDLE_LIMIT then
					vehicle:Destroy()
				end
			end
		end
	end
end)
```

## Testing it

1. Two clients from the **Test** tab. Spawn from both, confirm two vehicles exist.
2. Spawn repeatedly from one client — the count should stay at one.
3. Click faster than the cooldown — extra requests should be ignored, not queued.
4. Leave with one client. Its vehicle should disappear.
5. Check `Workspace.SpawnedVehicles` in the Explorer while testing. That folder is
   the whole truth about what exists.

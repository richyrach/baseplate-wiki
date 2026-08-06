---
title: "RemoteEvent vs RemoteFunction: which one to use, and when the difference bites"
description: Choosing between the two without freezing scripts, trusting the client, or making networking harder than it needs to be.
date: 2026-08-06
category: Scripting
kind: learn
level: Intermediate
minutes: 14
---

`RemoteEvent` and `RemoteFunction` both move information between the client and
server, so they can look interchangeable at first.

They are not.

The important difference is not that one is for "events" and the other is for
"functions." The real difference is whether the script sending the request has to
stop and wait for a response.

A `RemoteEvent` sends information and continues immediately. A `RemoteFunction`
sends information and yields until the other side returns something. Roblox
describes RemoteEvents as asynchronous, one-way communication and RemoteFunctions
as synchronous, two-way communication.

That one difference can decide whether your game feels responsive or randomly
freezes.

## The rule I actually use

Use a `RemoteEvent` when you are telling the other side that something happened.

Use a `RemoteFunction` when you are asking the other side a question and genuinely
need the answer before the current code can continue.

| Situation | Use |
|---|---|
| The player clicked an attack button | `RemoteEvent` |
| The player touched an interaction prompt | `RemoteEvent` |
| The server tells the client to show an effect | `RemoteEvent` |
| The server updates a player's quest UI | `RemoteEvent` |
| The client requests its current inventory | `RemoteFunction` |
| The client asks whether a purchase succeeded | `RemoteFunction` |
| The client needs data before opening a menu | Usually `RemoteFunction` |
| The server asks the client for an important answer | Usually neither; redesign it |

The last row matters more than it looks. The server should not depend on a client
returning an important result.

## RemoteEvent: send it and keep going

A `RemoteEvent` does not return a value. From a LocalScript, you use
`FireServer()`:

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local remotes = ReplicatedStorage:WaitForChild("Remotes")
local equipItem = remotes:WaitForChild("EquipItem")

equipItem:FireServer("WoodenSword")
print("The request was sent")
```

The `print()` runs immediately after the request is sent. It does not wait for the
server to equip the item.

On the server, you listen through `OnServerEvent`:

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local remotes = ReplicatedStorage:WaitForChild("Remotes")
local equipItem = remotes:WaitForChild("EquipItem")

local allowedItems = {
	WoodenSword = true,
	TrainingBow = true,
}

equipItem.OnServerEvent:Connect(function(player, itemName)
	if typeof(itemName) ~= "string" then
		return
	end
	if not allowedItems[itemName] then
		return
	end

	local inventory = player:FindFirstChild("Inventory")
	if not inventory or not inventory:FindFirstChild(itemName) then
		return
	end

	print(player.Name .. " equipped " .. itemName)
end)
```

When a client fires a RemoteEvent, Roblox automatically passes that client's
`Player` object as the first argument of `OnServerEvent`. The client does not need
to send its own player object.

This is wrong:

```lua
equipItem:FireServer(game.Players.LocalPlayer, "WoodenSword")
```

It would cause the server to receive two player-related arguments:

```lua
equipItem.OnServerEvent:Connect(function(realPlayer, sentPlayer, itemName)
	-- realPlayer was added by Roblox
	-- sentPlayer was manually sent by the client
end)
```

Just send the information that the server needs to inspect.

## Sending an event back to the client

RemoteEvents are one-way per call, but they can communicate in either direction.
The server can send information to one client with `FireClient()`:

```lua
local equipmentChanged = remotes:WaitForChild("EquipmentChanged")
equipmentChanged:FireClient(player, itemName)
```

The client receives it through `OnClientEvent`:

```lua
local equipmentChanged = remotes:WaitForChild("EquipmentChanged")

equipmentChanged.OnClientEvent:Connect(function(itemName)
	print("The server equipped:", itemName)
end)
```

The server can also use `FireAllClients()`:

```lua
roundStarted:FireAllClients(120)
```

Every connected client listening to that RemoteEvent receives the value. This is
useful for announcements, round timers, visual effects and other updates that do
not require the sender to wait for a returned value.

## RemoteFunction: send a request and wait for the result

A `RemoteFunction` returns one or more values. From a LocalScript, call
`InvokeServer()`:

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local remotes = ReplicatedStorage:WaitForChild("Remotes")
local getInventory = remotes:WaitForChild("GetInventory")

local inventory = getInventory:InvokeServer()
print("Inventory received")
```

The LocalScript stops at `InvokeServer()` until the server returns a result.

The server handles the request with `OnServerInvoke`:

```lua
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local remotes = ReplicatedStorage:WaitForChild("Remotes")
local getInventory = remotes:WaitForChild("GetInventory")

local playerInventories = {
	-- Filled by the game's data system
}

getInventory.OnServerInvoke = function(player)
	local inventory = playerInventories[player]
	if not inventory then
		return {}
	end
	return table.clone(inventory)
end
```

As with `OnServerEvent`, Roblox automatically provides the invoking player as the
first argument.

Unlike an event connection, `OnServerInvoke` is assigned directly. You do not use
`:Connect()`:

```lua
getInventory.OnServerInvoke = function(player)
	return {}
end
```

Do not do this:

```lua
getInventory.OnServerInvoke:Connect(function(player)
	return {}
end)
```

`OnServerInvoke` is a callback, not an event signal.

## Protecting an invocation with pcall

If the server callback errors, the invocation can fail. Code that depends on the
result should handle that possibility.

```lua
local success, result = pcall(function()
	return getInventory:InvokeServer()
end)

if not success then
	warn("Could not load inventory:", result)
	return
end

local inventory = result
```

This prevents the rest of that LocalScript path from crashing because the
invocation failed.

> [!warning]
> `pcall` does not turn a RemoteFunction into an asynchronous request. The script
> still waits for the server to answer. All it does is stop an error inside the
> server callback from taking your client code down with it.

## When RemoteFunction is the correct choice

A RemoteFunction is reasonable when all of these are true:

1. The caller needs a returned value.
2. The answer should be available quickly.
3. The current action cannot continue correctly without that answer.
4. The server can calculate the answer without waiting on a long operation.

Opening an inventory menu is a common example:

```lua
local success, inventory = pcall(function()
	return getInventory:InvokeServer()
end)

if not success then
	errorLabel.Text = "Could not load inventory"
	return
end

drawInventory(inventory)
inventoryFrame.Visible = true
```

The menu needs the inventory before it can draw the item buttons. Waiting for a
short server response makes sense.

A shop purchase can also use a RemoteFunction when the client needs an immediate
result:

```lua
local purchaseItem = remotes:WaitForChild("PurchaseItem")

local success, purchased, message = pcall(function()
	return purchaseItem:InvokeServer("HealthPotion")
end)

if not success then
	statusLabel.Text = "The request failed"
elseif purchased then
	statusLabel.Text = "Purchased"
else
	statusLabel.Text = message
end
```

The server still decides whether the purchase is allowed:

```lua
local prices = {
	HealthPotion = 50,
}

purchaseItem.OnServerInvoke = function(player, itemName)
	if typeof(itemName) ~= "string" then
		return false, "Invalid item"
	end

	local price = prices[itemName]
	if not price then
		return false, "Item does not exist"
	end

	local coins = player:FindFirstChild("Coins")
	if not coins or coins.Value < price then
		return false, "Not enough coins"
	end

	coins.Value -= price
	return true, "Purchase completed"
end
```

The client asks to purchase an item. The server checks the item, price and
balance. The client does not get to declare that the purchase succeeded.

## When RemoteFunction is the wrong choice

Do not use a RemoteFunction just because returning `true` feels convenient. These
actions normally belong on RemoteEvents:

```lua
attackRequested:FireServer()
doorInteraction:FireServer(door)
vehicleHorn:FireServer(true)
readyStatusChanged:FireServer(true)
```

The client does not need to pause until the server says, "Yes, I heard you."

For example, this is usually a bad firing system:

```lua
local accepted = fireWeapon:InvokeServer(targetPosition)
if accepted then
	playRecoil()
end
```

Every shot pauses the LocalScript while it waits for a network round trip. A
player with higher latency will feel that delay more strongly.

A better structure is:

```lua
playRecoil()
fireWeapon:FireServer(targetPosition)
```

The server then validates the shot and applies the real damage. The client can
display immediate visual feedback, but the server remains responsible for the
result that affects gameplay.

## The difference bites when everything works in Studio

A RemoteFunction looks like a normal ModuleScript function: one line, get a
result, continue. That is exactly why it gets misused. And in Studio the test
client and server run on the same computer, so the wait is close to zero and
nothing looks wrong.

The problem shows up once the server callback does real work. A menu button calls
`InvokeServer()`, the callback waits for data, and the entire button handler stops
at that line. The button is not broken. The LocalScript is waiting.

That is the annoying part of this bug: there may be no red error at all.

When an interface sometimes feels dead, search your LocalScripts for:

```lua
:InvokeServer()
```

Then check what the server callback does before it returns.

<!-- OWN_EXPERIENCE -->

## Long work should not hold a RemoteFunction open

A RemoteFunction callback should return quickly. Avoid using one for work such as:

- generating a large map
- waiting for another player
- running matchmaking
- retrying a DataStore request several times
- waiting for a countdown
- processing a long queue

For a longer operation, use a RemoteEvent to start the request and another
RemoteEvent to send the result later.

Client:

```lua
local generateReport = remotes:WaitForChild("GenerateReport")
local reportReady = remotes:WaitForChild("ReportReady")

generateReport:FireServer()
statusLabel.Text = "Generating..."

reportReady.OnClientEvent:Connect(function(report)
	statusLabel.Text = "Ready"
	showReport(report)
end)
```

Server:

```lua
local generateReport = remotes:WaitForChild("GenerateReport")
local reportReady = remotes:WaitForChild("ReportReady")

generateReport.OnServerEvent:Connect(function(player)
	local report = buildReportFor(player)
	if player.Parent then
		reportReady:FireClient(player, report)
	end
end)
```

Now the client can keep running while the server works. For a serious request
system, include a request ID so the client can match each response to the correct
request.

## Be careful with InvokeClient

A server Script can call a client RemoteFunction:

```lua
local answer = remoteFunction:InvokeClient(player)
```

In most gameplay systems, this is a bad dependency. The server cannot trust the
client's answer — an exploiter controls their client and can return whatever value
benefits them.

There is also a reliability problem. Roblox warns that `InvokeClient()` throws an
error if the client disconnects during the invocation. If the client never returns
a value, the server can yield forever.

Do not make the server ask questions such as:

```lua
local didPlayerHitTarget = verifyHit:InvokeClient(player)
local canPlayerAffordItem = checkCoins:InvokeClient(player)
local isPlayerAllowedInside = checkPermission:InvokeClient(player)
```

Those decisions belong on the server.

Use a RemoteEvent when the server only needs to tell the client to do something
visual:

```lua
showNotification:FireClient(player, "You unlocked a new area")
```

The server sends the instruction and continues. It does not depend on the client
responding.

## Neither remote type makes client data trustworthy

Changing a RemoteEvent into a RemoteFunction does not improve security.

Both can be fired or invoked with fake arguments by an exploiter. Validate every
value received from a client before using it: permission checks, type checks,
range checks, rate limits, and checks against the actual server state.

Never accept this:

```lua
giveCoins.OnServerEvent:Connect(function(player, amount)
	player.Coins.Value += amount
end)
```

The client could send any number it wants.

Instead, the client should report an action:

```lua
collectCoin.OnServerEvent:Connect(function(player, coin)
	-- Check that coin is a real collectible.
	-- Check that the player is close enough.
	-- Check that it has not already been collected.
	-- Then award the amount stored on the server.
end)
```

The remote carries a request. It does not carry authority.

## Common mistakes

### Expecting FireServer to return something

This does not work:

```lua
local result = purchaseItem:FireServer("HealthPotion")
```

`result` will not contain a server response. `FireServer()` does not return the
result of `OnServerEvent`. Use a RemoteFunction when the immediate result is
required, or send the result back through another RemoteEvent.

### Forgetting to return from OnServerInvoke

This callback returns `nil`:

```lua
getCoins.OnServerInvoke = function(player)
	local coins = player.Coins.Value
end
```

It calculated the value but never returned it. Correct version:

```lua
getCoins.OnServerInvoke = function(player)
	return player.Coins.Value
end
```

### Connecting to OnServerInvoke

This is wrong:

```lua
remoteFunction.OnServerInvoke:Connect(function(player)
	return true
end)
```

Assign the callback instead:

```lua
remoteFunction.OnServerInvoke = function(player)
	return true
end
```

### Overwriting the callback

A RemoteFunction has one `OnServerInvoke` callback. This second assignment
replaces the first one:

```lua
getData.OnServerInvoke = function(player)
	return "First result"
end

getData.OnServerInvoke = function(player)
	return "Second result"
end
```

Organise the logic inside one callback, or call functions from a ModuleScript.

### Putting remotes somewhere only one side can access

Both sides must be able to find the remote. `ReplicatedStorage` is the normal
location:

```text
ReplicatedStorage
└── Remotes
    ├── EquipItem
    ├── EquipmentChanged
    └── GetInventory
```

A LocalScript cannot access a RemoteEvent stored in `ServerStorage`.

## A simple decision checklist

Before creating a remote, ask:

**Does the caller need a returned value before continuing?** No: use a
`RemoteEvent`. Yes: continue to the next question.

**Can the result arrive later without blocking the current code?** Yes: use one
RemoteEvent for the request and another for the response. No: a `RemoteFunction`
may fit.

**Is the server invoking a client and waiting for its answer?** Redesign it,
unless the returned data is completely non-authoritative and failure is safely
handled.

**Does the request affect currency, damage, inventory, progression or another
player?** Validate everything on the server, no matter which remote type you
chose.

## Final pattern

Use RemoteEvents for commands and notifications:

```lua
remoteEvent:FireServer(...)
remoteEvent.OnServerEvent:Connect(function(player, ...)
end)

remoteEvent:FireClient(player, ...)
remoteEvent.OnClientEvent:Connect(function(...)
end)
```

Use RemoteFunctions for short request-and-response operations:

```lua
local result = remoteFunction:InvokeServer(...)

remoteFunction.OnServerInvoke = function(player, ...)
	return result
end
```

The easiest way to remember the difference:

A RemoteEvent says, "This happened." A RemoteFunction asks, "What is the answer?"

When you only need to send information, prefer the RemoteEvent. When you truly
need an immediate returned value, use the RemoteFunction and remember that the
calling script will wait.

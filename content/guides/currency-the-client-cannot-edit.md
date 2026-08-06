---
title: "A currency system the client cannot edit"
description: Where the number lives, who is allowed to change it, and the request shape that stops players awarding themselves money.
date: 2026-08-06
category: Scripting
kind: learn
level: Intermediate
minutes: 11
---

Every game with money eventually gets a player who has an impossible amount of it.
It is almost always the same mistake, and it is a design mistake rather than a
missing security feature.

## The mistake

```lua
-- LocalScript
local coins = 0

coinPart.Touched:Connect(function()
	coins += 10
	updateCoins:FireServer(coins)     -- "here is my new total"
end)
```

```lua
-- ServerScriptService
updateCoins.OnServerEvent:Connect(function(player, newTotal)
	player.leaderstats.Coins.Value = newTotal
end)
```

The server is being *told* the answer. A player can fire that remote with any number
they like, from the developer console or an injected script, and the server will
write it down. No amount of validation on the number fixes this, because there is no
legitimate value to compare against — the server never computed one.

## The shape that works

The client reports **what happened**. The server decides **what it is worth**.

```lua
-- LocalScript: no amount, just which coin
coinPart.Touched:Connect(function(hit)
	if hit.Parent == player.Character then
		collectCoin:FireServer(coinPart)
	end
end)
```

```lua
-- ServerScriptService
local COIN_VALUE = 10
local MAX_REACH = 14

local collected = {}     -- [coinPart] = true

collectCoin.OnServerEvent:Connect(function(player, coin)
	-- 1. is it the right kind of thing at all?
	if typeof(coin) ~= "Instance" or not coin:IsA("BasePart") then
		return
	end

	-- 2. is it actually one of our coins?
	if not coin:IsDescendantOf(workspace.Coins) then
		return
	end

	-- 3. has it already been taken?
	if collected[coin] then
		return
	end

	-- 4. is the player near enough to plausibly have touched it?
	local character = player.Character
	if not character or not character.PrimaryPart then
		return
	end
	if (character.PrimaryPart.Position - coin.Position).Magnitude > MAX_REACH then
		return
	end

	-- only now does anything change
	collected[coin] = true
	coin:Destroy()
	addBalance(player, COIN_VALUE)
end)
```

Four checks, and each one closes a specific attack:

1. **Type check.** Prevents a crash, and stops arbitrary objects being passed.
2. **Membership check.** Stops a player passing a coin-shaped part they created
   themselves.
3. **Double-spend check.** Stops the same coin being claimed twenty times in one
   frame. `OnServerEvent` can be called as fast as the attacker likes.
4. **Distance check.** Stops a player collecting every coin on the map from spawn.

The amount — `COIN_VALUE` — never crosses the network. It only exists on the server.

## Where the balance lives

Not in `leaderstats`. That is a display surface. Keep the real number in a server-only
table and mirror it out:

```lua
-- ServerScriptService/Economy.server.lua
local Players = game:GetService("Players")

local balances = {}     -- [userId] = number

local function getBalance(player)
	return balances[player.UserId] or 0
end

local function mirror(player)
	local stats = player:FindFirstChild("leaderstats")
	local coins = stats and stats:FindFirstChild("Coins")
	if coins then
		coins.Value = getBalance(player)
	end
end

local function addBalance(player, amount)
	if type(amount) ~= "number" or amount ~= amount then   -- NaN check
		return false
	end
	amount = math.floor(amount)

	local current = getBalance(player)
	local newValue = math.clamp(current + amount, 0, 1e12)

	balances[player.UserId] = newValue
	mirror(player)
	return true
end

local function trySpend(player, cost)
	if type(cost) ~= "number" or cost <= 0 then
		return false
	end
	local current = getBalance(player)
	if current < cost then
		return false
	end

	balances[player.UserId] = current - cost
	mirror(player)
	return true
end
```

Details worth keeping:

- **`amount ~= amount`** is the NaN test. `NaN` propagates through arithmetic and can
  corrupt a balance permanently, and it survives a DataStore round trip.
- **`math.floor`** stops fractional currency appearing from any source that produces
  a float.
- **`math.clamp`** with an upper bound catches overflow-style bugs before they reach
  the save file.
- **`trySpend` returns a boolean.** Callers must check it. A spend function that
  silently does nothing on failure produces free items.

## Spending

```lua
local prices = {
	HealthPotion = 50,
	SpeedBoost = 120,
}

buyItem.OnServerInvoke = function(player, itemName)
	if typeof(itemName) ~= "string" then
		return false, "Invalid request"
	end

	local price = prices[itemName]
	if not price then
		return false, "No such item"
	end

	if not trySpend(player, price) then
		return false, "Not enough coins"
	end

	grantItem(player, itemName)
	return true, "Purchased"
end
```

The client sends an item **name**, looked up in a server-side price table. It never
sends a price. This is the same principle as the coin: names in, values decided
server-side.

## Rate limiting

Every remote a client can fire needs a floor on how often:

```lua
local lastCall = {}
local MIN_INTERVAL = 0.1

local function rateLimited(player)
	local now = os.clock()
	local last = lastCall[player.UserId]
	if last and now - last < MIN_INTERVAL then
		return true
	end
	lastCall[player.UserId] = now
	return false
end
```

Check it first thing in every handler. Without this, even a correct handler can be
used to pin your server's CPU at 100%.

Clean up on leave, or these tables grow forever:

```lua
Players.PlayerRemoving:Connect(function(player)
	balances[player.UserId] = nil
	lastCall[player.UserId] = nil
end)
```

## Client-side prediction is fine

Showing the new balance instantly, before the server confirms, is good practice — it
makes the game feel responsive. Just treat it as a guess:

```lua
-- LocalScript
local displayed = 0

local function optimisticAdd(amount)
	displayed += amount
	redraw()
end

-- the server's number always wins
coinsValue.Changed:Connect(function()
	displayed = coinsValue.Value
	redraw()
end)
```

The client displays; the server decides. When they disagree, the server is right.

> [!warning]
> Do not put your price table in `ReplicatedStorage` if the prices are meant to be
> authoritative. Clients can read everything in there. The client can have a copy for
> display; the server must use its own.

## The audit

Go through every remote in your game and ask:

1. Does the client send an **amount**, a **price**, or a **total**? If yes, that is
   the bug. Change it to send an identifier and look the value up server-side.
2. Is there a rate limit?
3. Is there a type check on every argument?
4. For anything world-related, is there a distance or possession check?
5. Can the same request be replayed to get the reward twice?
6. Does the authoritative number live in a server-only table, rather than in
   `leaderstats` or a `Value` object the client can see?

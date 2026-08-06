---
title: "Developer products and ProcessReceipt without double-granting"
description: Repeatable purchases need a receipt handler that records what it granted. Get this wrong and players either lose Robux or get free items forever.
date: 2026-08-06
category: Monetization
kind: learn
level: Advanced
minutes: 14
---

A **game pass** is bought once and owned forever. A **developer product** can be
bought repeatedly — 100 coins, a revive, a booster.

That difference is the whole reason developer products are harder. There is no
"owns it" flag to check, so the only record that a purchase happened is the receipt
Roblox hands you, and you have to handle it correctly or one of two things happens:

- You grant without recording, and Roblox re-sends the receipt → the player gets the
  item **twice** for one payment.
- You return the wrong value, and Roblox thinks it failed → the player is **charged
  and gets nothing**.

Both are real money. This is the one system in Roblox where "roughly right" is not
acceptable.

## How the callback works

`MarketplaceService.ProcessReceipt` is a **callback**, not an event. There is exactly
one, it must be assigned (not connected), and it must live on the server.

```lua
MarketplaceService.ProcessReceipt = processReceipt   -- assignment
```

Roblox calls it after taking the player's Robux. Your job is to grant the item and
return a `Enum.ProductPurchaseDecision`:

- **`PurchaseGranted`** — done, do not call me again about this receipt.
- **`NotProcessedYet`** — I could not grant it. Roblox retries later, including on
  the player's next join.

If your function errors, or returns nothing, Roblox treats it as not granted and will
call again. That retry behaviour is a safety net for the player and the source of the
double-grant bug for you.

## The receipt

`receiptInfo` is a table containing, among other fields:

| Field | Meaning |
|---|---|
| `PurchaseId` | unique ID for **this transaction** |
| `PlayerId` | the buyer's `UserId` |
| `ProductId` | which developer product |
| `CurrencySpent` | how much |
| `CurrencyType` | which currency |

`PurchaseId` is the important one. It is the only thing that lets you tell "a new
purchase" from "the same purchase, sent again."

## The implementation

```lua
-- ServerScriptService/Receipts.server.lua
local MarketplaceService = game:GetService("MarketplaceService")
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")

local purchaseHistory = DataStoreService:GetDataStore("PurchaseHistory_v1")

-- what each product does. Each handler returns true only on success.
local productHandlers = {
	[111111111] = function(player)          -- 100 coins
		return addBalance(player, 100)
	end,

	[222222222] = function(player)          -- revive
		local character = player.Character
		if not character then
			return false                     -- cannot grant right now
		end
		local humanoid = character:FindFirstChildOfClass("Humanoid")
		if not humanoid or humanoid.Health > 0 then
			return false
		end
		humanoid.Health = humanoid.MaxHealth
		return true
	end,
}

local function processReceipt(receiptInfo)
	local playerId = receiptInfo.PlayerId
	local productId = receiptInfo.ProductId
	local purchaseKey = receiptInfo.PurchaseId

	local player = Players:GetPlayerByUserId(playerId)
	if not player then
		-- They left. Do not grant to nobody, and do not mark it done.
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end

	local handler = productHandlers[productId]
	if not handler then
		warn("[Receipt] no handler for product", productId)
		-- Deliberately NotProcessedYet: a missing handler is a bug on our side,
		-- and retrying means we can ship the fix and the player still gets it.
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end

	-- has this exact transaction already been granted?
	local alreadyGranted = false
	local ok, err = pcall(function()
		purchaseHistory:UpdateAsync(purchaseKey, function(existing)
			if existing then
				alreadyGranted = true
				return existing              -- leave it alone
			end
			return true                       -- claim it
		end)
	end)

	if not ok then
		warn("[Receipt] history check failed:", err)
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end

	if alreadyGranted then
		-- A duplicate delivery of a receipt we already honoured.
		return Enum.ProductPurchaseDecision.PurchaseGranted
	end

	local granted = false
	local handlerOk, handlerErr = pcall(function()
		granted = handler(player)
	end)

	if not handlerOk then
		warn("[Receipt] handler errored:", handlerErr)
	end

	if not granted then
		-- Release our claim so the retry can succeed.
		pcall(function()
			purchaseHistory:RemoveAsync(purchaseKey)
		end)
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end

	return Enum.ProductPurchaseDecision.PurchaseGranted
end

MarketplaceService.ProcessReceipt = processReceipt
```

## Why it is shaped like that

**`UpdateAsync` keyed on `PurchaseId`, not `SetAsync`.** The check and the claim must
be one atomic operation. With `GetAsync` then `SetAsync`, two servers processing the
same retry can both read "not granted" and both grant.

**Claim first, grant second.** If you grant first and then record, a crash between
the two loses the record and the retry grants again.

**Release the claim if granting fails.** This is the step almost every tutorial
misses. If you claim the `PurchaseId` and then the handler fails, the claim makes
every future retry look like a duplicate — and the player never gets their item. The
`RemoveAsync` undoes the claim so the retry can work.

**Return `PurchaseGranted` on a detected duplicate.** The player has already been
given the item. Saying `NotProcessedYet` asks Roblox to try forever.

**`NotProcessedYet` for a missing handler.** Counter-intuitive, but right: it means
you can ship the handler tomorrow and the player still receives what they paid for.
Returning `PurchaseGranted` would discard their money silently.

> [!warning]
> Never return `PurchaseGranted` on a path where the item was not actually given. It
> is not a "close the transaction" value — it is a promise that the player has their
> goods, and it is the last time Roblox will ask you.

## Prompting the purchase

```lua
-- client
MarketplaceService:PromptProductPurchase(player, PRODUCT_ID)
```

The product ID comes from the Creator Dashboard, under Monetization → Developer
Products. It is not the same kind of ID as a game pass.

## Do not grant from PromptProductPurchaseFinished

```lua
-- for UI feedback only
MarketplaceService.PromptProductPurchaseFinished:Connect(
	function(userId, productId, isPurchased)
		-- close a menu, play a sound. Grant NOTHING here.
	end
)
```

This event tells you the prompt closed. It is not the payment confirmation, it does
not carry a `PurchaseId`, and it cannot be de-duplicated. `ProcessReceipt` is the
only authoritative signal that money changed hands.

## Testing

Developer product purchases **do not work in Studio**. You must test in a published
game, and real purchases cost real Robux — though purchases you make in your own game
largely return to you, minus Roblox's cut.

What you can test cheaply is the logic, by calling your handler directly:

```lua
-- Studio only, temporary
local fakeReceipt = {
	PurchaseId = "test-" .. os.time(),
	PlayerId = game.Players:GetPlayers()[1].UserId,
	ProductId = 111111111,
	CurrencySpent = 25,
}
print(processReceipt(fakeReceipt))
```

Run it twice with the **same** `PurchaseId` and confirm the second call returns
`PurchaseGranted` without granting again. That is the duplicate path, which is the
one that costs you money if it is wrong, and it is the one you can verify for free.

Delete this before publishing.

## A note on BindReceiptHandler

`MarketplaceService:BindReceiptHandler(transactionType, handler, filter)` is a newer
addition that returns a connection and allows more than one handler, filtered by
transaction type. It is the direction Roblox is heading, particularly for
subscriptions and bulk purchases.

I have not used it in a shipped game, so I am not going to present a pattern for it
here as though I had. If you are starting fresh, it is worth reading the current
reference page for it — but the `ProcessReceipt` logic above, especially the
claim-and-release ordering, is the part that matters regardless of which entry point
delivers the receipt.

<!-- OWN_EXPERIENCE -->

## The audit

1. Is the de-duplication keyed on `PurchaseId`?
2. Is the claim made with `UpdateAsync`, not `GetAsync` + `SetAsync`?
3. Is the claim **released** when granting fails?
4. Does a detected duplicate return `PurchaseGranted`?
5. Does every failure path return `NotProcessedYet` rather than erroring?
6. Is `ProcessReceipt` **assigned** once, on the server, and never in more than one
   script? A second assignment silently replaces the first, and the products in the
   replaced table stop working.

---
term: MarketplaceService
category: Monetization
summary: Handles game passes, developer products and receipts. Several of its most-used methods are now deprecated in favour of Async versions.
---

`MarketplaceService` is the entry point for everything involving Robux. It is also
one of the services where the most widely-copied tutorial code is now calling
deprecated methods.

## The deprecations, as of August 2026

| Deprecated | Use instead |
|---|---|
| `GetProductInfo()` | `GetProductInfoAsync()` |
| `PlayerOwnsAsset()` | `PlayerOwnsAssetAsync()` |
| `PlayerOwnsBundle()` | `PlayerOwnsBundleAsync()` |
| `PromptPremiumPurchase()` | deprecated; no confirmed replacement |

If you copied a monetization script from a video, it very likely uses at least one of
these. They still work, which is exactly why nobody notices.

## What is current

```lua
local MarketplaceService = game:GetService("MarketplaceService")

-- game passes
MarketplaceService:PromptGamePassPurchase(player, gamePassId)
MarketplaceService:UserOwnsGamePassAsync(userId, gamePassId)   -- yields

-- developer products
MarketplaceService:PromptProductPurchase(player, productId)

-- info about either
MarketplaceService:GetProductInfoAsync(assetId, infoType)      -- yields
```

`infoType` is an `Enum.InfoType` — `GamePass`, `Product`, `Asset`, `Bundle`,
`Subscription`. Passing the wrong one returns data that looks plausible and has the
wrong price in it.

## Every Async method needs a pcall

These are web requests. They fail.

```lua
local ok, owns = pcall(function()
	return MarketplaceService:UserOwnsGamePassAsync(player.UserId, PASS_ID)
end)

if not ok then
	warn("check failed:", owns)
	return              -- do NOT treat this as "does not own"
end
```

Collapsing a failed check into `false` means prompting someone who already paid.
Collapsing it into `true` means giving the benefit away. Treat failure as its own
third state.

## The events are for UI only

```lua
MarketplaceService.PromptGamePassPurchaseFinished:Connect(
	function(player, gamePassId, wasPurchased) end
)
MarketplaceService.PromptProductPurchaseFinished:Connect(
	function(userId, productId, isPurchased) end
)
```

Note the inconsistency: the game pass event gives you a **`player`**, the product event
gives you a **`userId`**. Getting this wrong produces code that looks right and errors
at runtime.

Both fire for every player when connected on the server, so filter on the arguments.
And neither is a payment confirmation — for developer products, only `ProcessReceipt`
is authoritative.

## ProcessReceipt is a callback, not an event

```lua
MarketplaceService.ProcessReceipt = handler       -- assign
```

There is exactly one, it must be assigned rather than connected, and a second
assignment anywhere in your codebase silently replaces the first. If some products
stopped granting after you added a script, look for a second assignment.

It must return an `Enum.ProductPurchaseDecision`: `PurchaseGranted` or
`NotProcessedYet`. Returning nothing, or erroring, counts as not granted and Roblox
retries — which is why de-duplicating on `receiptInfo.PurchaseId` is mandatory.

## Newer surface worth knowing about

`BindReceiptHandler(transactionType, handler, filter)` returns a connection and allows
multiple filtered handlers. `PromptSubscriptionPurchase` and `PromptBulkPurchase`
exist for subscriptions and multi-item carts.

These are newer than the patterns most guides cover, including this site's. Check the
current reference before building on them.

## Nothing works in Studio

Purchase prompts appear in Studio and never complete. `ProcessReceipt` never fires.
Monetization can only be tested in a published place, and real purchases cost real
Robux — though purchases in your own game largely return to you.

Test the *logic* by calling your receipt handler directly with a fake receipt table,
then delete that code before publishing.

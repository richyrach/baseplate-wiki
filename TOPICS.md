# The guide plan

48 guides, 31 written. Generated from `topics.py` -- edit that file and run `python3 gen_prompts.py` rather than editing this one.

Every category has at least two published guides, so no section of the nav leads to an empty page. Remaining topics can be written in any order — pick whichever you have actually hit recently, since that is where your own notes will be freshest.

## Scripting (8)

- [x] 01 — Your script works in Studio but breaks in the real game  
      `learn` · `Beginner`
- [x] 02 — RemoteEvent vs RemoteFunction: which to use, and when the difference bites  
      `learn` · `Intermediate`
- [x] 03 — 'X is not a valid member of Y': every cause, in order of likelihood  
      `learn` · `Beginner`
- [ ] 04 — Why WaitForChild hangs forever, and the timeout pattern that fixes it  
      `learn` · `Beginner`
- [x] 05 — A currency system the client cannot edit  
      `learn` · `Intermediate`
- [x] 06 — The Developer Console (F9): finding errors Studio never showed you  
      `learn` · `Beginner`
- [ ] 46 — A sprint and stamina system that the server agrees with  
      `recipe` · `Intermediate`
- [ ] 48 — Chat commands and a simple admin system  
      `recipe` · `Intermediate`

## Building (5)

- [x] 07 — Welds, WeldConstraints and Anchored: why your build falls apart on Play  
      `learn` · `Beginner`
- [x] 08 — Moving a model without it exploding: PrimaryPart and PivotTo  
      `recipe` · `Intermediate`
- [ ] 09 — Unions and negate parts: when CSG quietly ruins your model  
      `learn` · `Intermediate`
- [x] 38 — A day and night cycle that looks good and stays in sync  
      `recipe` · `Intermediate`
- [ ] 47 — Sound and music zones that cross-fade  
      `recipe` · `Intermediate`

## Vehicles (4)

- [ ] 10 — Getting A-Chassis into a car you built yourself  
      `recipe` · `Intermediate`
- [x] 11 — Why your car flips, sinks, or drives like it's on ice  
      `learn` · `Intermediate`
- [x] 12 — Spawning one vehicle per player and cleaning up the old one  
      `recipe` · `Intermediate`
- [ ] 13 — A working speedometer: reading velocity without lag  
      `recipe` · `Beginner`

## UI (6)

- [x] 14 — Scale vs Offset: a GUI that survives phone screens  
      `learn` · `Beginner`
- [x] 15 — Why your button works in Studio but does nothing on mobile  
      `learn` · `Beginner`
- [ ] 16 — A shop menu the server actually validates  
      `recipe` · `Intermediate`
- [x] 39 — A clock UI that shows in-game time without redrawing every frame  
      `recipe` · `Beginner`
- [x] 40 — Dynamic UI: one function that draws your interface from state  
      `learn` · `Intermediate`
- [x] 43 — A notification system: server-triggered toasts that stack  
      `recipe` · `Intermediate`

## Data (8)

- [x] 17 — Your first DataStore that doesn't lose player data  
      `learn` · `Intermediate`
- [x] 18 — 'DataStore request was added to queue': what throttling actually means  
      `learn` · `Intermediate`
- [ ] 19 — Saving on PlayerRemoving, and why it fails on server shutdown  
      `learn` · `Advanced`
- [ ] 20 — Session locking: stopping the same player's data loading twice  
      `learn` · `Advanced`
- [x] 21 — A leaderstats setup that shows the value you meant  
      `recipe` · `Beginner`
- [x] 41 — A global leaderboard with OrderedDataStore  
      `recipe` · `Advanced`
- [x] 42 — Awarding badges without spamming the API  
      `recipe` · `Intermediate`
- [x] 44 — A daily reward streak that cannot be cheated by changing the clock  
      `recipe` · `Intermediate`

## Multiplayer (4)

- [x] 22 — Teams and spawns without players landing on top of each other  
      `recipe` · `Beginner`
- [x] 23 — Round-based games: a timer loop that doesn't drift  
      `learn` · `Intermediate`
- [ ] 24 — What only breaks once real players are in the server  
      `learn` · `Intermediate`
- [ ] 45 — Teleporting players between places with TeleportAsync  
      `recipe` · `Intermediate`

## Animation (3)

- [x] 25 — Why your custom animation only plays for you  
      `learn` · `Intermediate`
- [x] 26 — TweenService vs lerp: smooth movement without a while loop  
      `recipe` · `Beginner`
- [ ] 27 — Rigging a custom character so Roblox animations still work  
      `recipe` · `Advanced`

## Monetization (6)

- [x] 32 — A game pass button that checks ownership before prompting  
      `recipe` · `Beginner`
- [x] 33 — Click a part to buy a game pass, with ProximityPrompt or ClickDetector  
      `recipe` · `Beginner`
- [x] 34 — Developer products and ProcessReceipt without double-granting  
      `learn` · `Advanced`
- [x] 35 — Giving Premium players benefits, and the Roblox Plus problem  
      `learn` · `Intermediate`
- [ ] 36 — Subscriptions with PromptSubscriptionPurchase  
      `learn` · `Advanced`
- [ ] 37 — A shop UI wired to developer products end to end  
      `recipe` · `Intermediate`

## Performance (4)

- [x] 28 — Why your game lags with 20 players when it was fine with 2  
      `learn` · `Intermediate`
- [ ] 29 — Reading the Roblox microprofiler without being scared of it  
      `learn` · `Advanced`
- [ ] 30 — StreamingEnabled: what breaks when you turn it on  
      `learn` · `Advanced`
- [x] 31 — The publishing checklist people forget before release  
      `recipe` · `Beginner`

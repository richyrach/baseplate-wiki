"""The guide plan: single source of truth for TOPICS.md and the ChatGPT prompts.

Edit this list, then run `python3 gen_prompts.py` to regenerate both files.

Every category in build.CATEGORIES needs at least two topics here, otherwise its
page ships empty and a reviewer clicking the nav lands on a thin page.
"""

# (topic, category, kind, level, done)
# kind: "learn" = teaching, read in order. "recipe" = one task, land and copy.
TOPICS = [
    # --- Scripting -----------------------------------------------------------
    ("Your script works in Studio but breaks in the real game",
     "Scripting", "learn", "Beginner", True),
    ("RemoteEvent vs RemoteFunction: which to use, and when the difference bites",
     "Scripting", "learn", "Intermediate", True),
    ("'X is not a valid member of Y': every cause, in order of likelihood",
     "Scripting", "learn", "Beginner", True),
    ("Why WaitForChild hangs forever, and the timeout pattern that fixes it",
     "Scripting", "learn", "Beginner", False),
    ("A currency system the client cannot edit",
     "Scripting", "learn", "Intermediate", True),
    ("The Developer Console (F9): finding errors Studio never showed you",
     "Scripting", "learn", "Beginner", True),

    # --- Building ------------------------------------------------------------
    ("Welds, WeldConstraints and Anchored: why your build falls apart on Play",
     "Building", "learn", "Beginner", True),
    ("Moving a model without it exploding: PrimaryPart and PivotTo",
     "Building", "recipe", "Intermediate", True),
    ("Unions and negate parts: when CSG quietly ruins your model",
     "Building", "learn", "Intermediate", False),

    # --- Vehicles ------------------------------------------------------------
    ("Getting A-Chassis into a car you built yourself",
     "Vehicles", "recipe", "Intermediate", False),
    ("Why your car flips, sinks, or drives like it's on ice",
     "Vehicles", "learn", "Intermediate", True),
    ("Spawning one vehicle per player and cleaning up the old one",
     "Vehicles", "recipe", "Intermediate", True),
    ("A working speedometer: reading velocity without lag",
     "Vehicles", "recipe", "Beginner", False),

    # --- UI ------------------------------------------------------------------
    ("Scale vs Offset: a GUI that survives phone screens",
     "UI", "learn", "Beginner", True),
    ("Why your button works in Studio but does nothing on mobile",
     "UI", "learn", "Beginner", True),
    ("A shop menu the server actually validates",
     "UI", "recipe", "Intermediate", False),

    # --- Data ----------------------------------------------------------------
    ("Your first DataStore that doesn't lose player data",
     "Data", "learn", "Intermediate", True),
    ("'DataStore request was added to queue': what throttling actually means",
     "Data", "learn", "Intermediate", True),
    ("Saving on PlayerRemoving, and why it fails on server shutdown",
     "Data", "learn", "Advanced", False),
    ("Session locking: stopping the same player's data loading twice",
     "Data", "learn", "Advanced", False),
    ("A leaderstats setup that shows the value you meant",
     "Data", "recipe", "Beginner", True),

    # --- Multiplayer ---------------------------------------------------------
    ("Teams and spawns without players landing on top of each other",
     "Multiplayer", "recipe", "Beginner", True),
    ("Round-based games: a timer loop that doesn't drift",
     "Multiplayer", "learn", "Intermediate", True),
    ("What only breaks once real players are in the server",
     "Multiplayer", "learn", "Intermediate", False),

    # --- Animation -----------------------------------------------------------
    ("Why your custom animation only plays for you",
     "Animation", "learn", "Intermediate", True),
    ("TweenService vs lerp: smooth movement without a while loop",
     "Animation", "recipe", "Beginner", True),
    ("Rigging a custom character so Roblox animations still work",
     "Animation", "recipe", "Advanced", False),

    # --- Performance ---------------------------------------------------------
    ("Why your game lags with 20 players when it was fine with 2",
     "Performance", "learn", "Intermediate", True),
    ("Reading the Roblox microprofiler without being scared of it",
     "Performance", "learn", "Advanced", False),
    ("StreamingEnabled: what breaks when you turn it on",
     "Performance", "learn", "Advanced", False),
    ("The publishing checklist people forget before release",
     "Performance", "recipe", "Beginner", True),

    # --- Monetization (written 6 Aug 2026, researched against current docs) ----
    ("A game pass button that checks ownership before prompting",
     "Monetization", "recipe", "Beginner", True),
    ("Click a part to buy a game pass, with ProximityPrompt or ClickDetector",
     "Monetization", "recipe", "Beginner", True),
    ("Developer products and ProcessReceipt without double-granting",
     "Monetization", "learn", "Advanced", True),
    ("Giving Premium players benefits, and the Roblox Plus problem",
     "Monetization", "learn", "Intermediate", True),
    ("Subscriptions with PromptSubscriptionPurchase",
     "Monetization", "learn", "Advanced", False),
    ("A shop UI wired to developer products end to end",
     "Monetization", "recipe", "Intermediate", False),

    # --- Added 6 Aug 2026 -----------------------------------------------------
    ("A day and night cycle that looks good and stays in sync",
     "Building", "recipe", "Intermediate", True),
    ("A clock UI that shows in-game time without redrawing every frame",
     "UI", "recipe", "Beginner", True),
    ("Dynamic UI: one function that draws your interface from state",
     "UI", "learn", "Intermediate", True),
    ("A global leaderboard with OrderedDataStore",
     "Data", "recipe", "Advanced", True),
    ("Awarding badges without spamming the API",
     "Data", "recipe", "Intermediate", True),
    ("A notification system: server-triggered toasts that stack",
     "UI", "recipe", "Intermediate", True),
    ("A daily reward streak that cannot be cheated by changing the clock",
     "Data", "recipe", "Intermediate", True),
    ("Teleporting players between places with TeleportAsync",
     "Multiplayer", "recipe", "Intermediate", False),
    ("A sprint and stamina system that the server agrees with",
     "Scripting", "recipe", "Intermediate", False),
    ("Sound and music zones that cross-fade",
     "Building", "recipe", "Intermediate", False),
    ("Chat commands and a simple admin system",
     "Scripting", "recipe", "Intermediate", False),
]

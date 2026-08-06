# Reference terms to write

44 entries. Curated, not generated — every one earns its page because
the official Roblox docs undersell something about it. The third column is the
angle that makes the entry worth existing; if you cannot deliver that angle, cut
the entry rather than padding it.

Read `CHATGPT-REFERENCE-BRIEF.md` before starting — especially the part about why
this list is 44 entries and not 200.

Write them in this order: the first ten are the ones your existing guides already
mention, so they light up the most auto-links immediately.

| # | Term | Category | The angle |
|---|---|---|---|
| 01 | `Script` | Scripting | server-side counterpart to LocalScript; where it runs |
| 02 | `ModuleScript` | Scripting | require() caching catches everyone out |
| 03 | `RemoteEvent` | Scripting | auto-passed player argument, one-way |
| 04 | `RemoteFunction` | Scripting | yields; InvokeClient is a trap |
| 05 | `FindFirstChild` | Scripting | vs WaitForChild vs direct indexing |
| 06 | `GetService` | Scripting | why game:GetService beats game.Players |
| 07 | `Instance.new` | Scripting | parent last, or you pay for re-parenting |
| 08 | `Destroy` | Scripting | vs :Remove(), and why connections outlive it |
| 09 | `Clone` | Scripting | Archivable, and what does not come along |
| 10 | `Connect` | Scripting | connections leak if never disconnected |
| 11 | `pcall` | Scripting | the only way to survive a DataStore error |
| 12 | `task.wait` | Scripting | vs wait(); why the old one is deprecated |
| 13 | `task.spawn` | Scripting | vs spawn() and coroutine.wrap |
| 14 | `RunService` | Scripting | Heartbeat vs RenderStepped vs Stepped |
| 15 | `tick` | Performance | deprecated; os.clock and workspace:GetServerTimeNow |
| 16 | `Players` | Scripting | PlayerAdded races on the server |
| 17 | `LocalPlayer` | Scripting | nil on the server, and why |
| 18 | `Character` | Scripting | CharacterAdded and respawn timing |
| 19 | `Humanoid` | Scripting | states, and why Health changes get rejected |
| 20 | `HumanoidRootPart` | Building | vs PrimaryPart, moving a character |
| 21 | `CFrame` | Building | position plus rotation; multiplication order matters |
| 22 | `Vector3` | Building | Magnitude, Unit, and comparing distances cheaply |
| 23 | `PivotTo` | Building | moving a model without breaking welds |
| 24 | `WeldConstraint` | Building | vs Weld vs Anchored |
| 25 | `Anchored` | Building | the single most common 'my build fell apart' |
| 26 | `CollectionService` | Building | tags instead of hard-coded paths |
| 27 | `Workspace` | Building | what replicates from it and what does not |
| 28 | `ServerStorage` | Data | invisible to clients; where secrets go |
| 29 | `DataStoreService` | Data | request budgets, and GetAsync failure |
| 30 | `UpdateAsync` | Data | vs SetAsync; the race it prevents |
| 31 | `leaderstats` | Data | the exact folder name the UI looks for |
| 32 | `ProfileService` | Data | session locking, and why people reach for it |
| 33 | `TweenService` | Animation | vs lerp in a loop; what cannot be tweened |
| 34 | `Animator` | Animation | why LoadAnimation on Humanoid is deprecated |
| 35 | `AnimationTrack` | Animation | Priority and weight, and why nothing plays |
| 36 | `UDim2` | UI | Scale vs Offset, the phone-screen bug |
| 37 | `AnchorPoint` | UI | the fix for 'my GUI is off centre' |
| 38 | `UIListLayout` | UI | LayoutOrder, and why AutomaticSize fights it |
| 39 | `ScreenGui` | UI | IgnoreGuiInset and ResetOnSpawn |
| 40 | `UserInputService` | UI | GameProcessedEvent, or you fire while typing |
| 41 | `Teams` | Multiplayer | TeamColor coupling and neutral spawns |
| 42 | `SpawnLocation` | Multiplayer | AllowTeamChangeOnTouch surprises |
| 43 | `StreamingEnabled` | Performance | what breaks the day you enable it |
| 44 | `MicroProfiler` | Performance | reading it without being scared |

## Already written

- `LocalScript` — Scripting
- `WaitForChild` — Scripting
- `ReplicatedStorage` — Scripting

## Filename convention

Lowercase, no punctuation: `content/terms/instance-new.md` for `Instance.new`,
`content/terms/task-wait.md` for `task.wait`. The `term:` field in the front
matter carries the correct casing for display and linking.
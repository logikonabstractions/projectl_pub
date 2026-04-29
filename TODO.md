# Project L — TODO

## Critical: Game cannot function properly

### 1. PlacePiece does not select valid configurations
`PlacePiece.perform_action()` picks a random configuration from the piece's cube with no check that it actually fits the card (mask + already occupied cells). Most placement attempts fail silently. Needs logic to filter the cube down to configurations valid for the current card state, then select one.

- **File**: `ProjectL/actions.py` — `PlacePiece.perform_action()`
- **Priority**: Class 1
- **Complexity**: 2

### 2. TakeCard is disconnected from the game's card pool
`TakeCard.perform_action()` creates a default `Card()` with a hardcoded mask instead of drawing from the game's configured card pool (`game_manager.cards`). Additionally, `is_action_valid()` blocks at >= 1 card, but real Project L allows up to 4 active cards.

- **File**: `ProjectL/actions.py` — `TakeCard`
- **Priority**: Class 1
- **Complexity**: 2

### 3. UpgradePiece is unimplemented
No `perform_action()` or `is_action_valid()` override. The `__init__` crashes with `IndexError` when `pieces` is empty due to an unguarded `random.choice(self.pieces)`.

- **File**: `ProjectL/actions.py` — `UpgradePiece`
- **Priority**: Class 1
- **Complexity**: 2

### 4. Master action is unimplemented
No logic at all. In real Project L, Master is a free end-of-turn action that places one piece on each of the player's active cards.

- **File**: `ProjectL/actions.py` — `Master`
- **Priority**: Class 1
- **Complexity**: 2

---

## Missing game systems

### 5. No scoring or winner declaration
`Player.full_cards` accumulates completed cards but nothing ever sums `card.reward.points`. No winner is declared at end of game. `GameManager.run()` just logs "Game ended."

- **Files**: `ProjectL/game_objects.py` — `GameManager.run()`, `Player`
- **Priority**: Class 1
- **Complexity**: 1

### 6. Completing a card does not grant the reward piece
When a card's `is_full` is set to `True`, the reward piece defined in `card.reward.piece` is never added to the player's inventory.

- **Files**: `ProjectL/strategies.py` — `BasicStrat._move_full_cards()`, `ProjectL/card.py` — `Card.place_piece()`
- **Priority**: Class 2
- **Complexity**: 1

### 7. No card pool / display mechanism
Real Project L has a visible row of available cards that get replenished from a deck. The game currently populates `game_manager.cards` from config but no action or player ever accesses it. `TakeCard` creates cards from nothing.

- **Files**: `ProjectL/game_objects.py` — `GameManager`, `ProjectL/actions.py` — `TakeCard`
- **Priority**: Class 1
- **Complexity**: 2

### 8. No piece level restriction on TakePiece
`TakePiece` lets the player take any piece of any level for free. In real Project L, free takes are restricted to level 1 pieces only. Higher level pieces require the `UpgradePiece` action (trade in a piece for one level higher).

- **Files**: `ProjectL/actions.py` — `TakePiece`
- **Priority**: Class 2
- **Complexity**: 1

### 9. No proper game-end trigger
Game ends only when `max_turns` is reached. In real Project L, the end is triggered by card deck depletion, followed by a "last round" where each player gets one final turn.

- **Files**: `ProjectL/game_objects.py` — `GameManager.run()`, `GameState`
- **Priority**: Class 2
- **Complexity**: 2

### 10. No free Master action at end of turn
In real Project L, after spending their 3 action points, every player gets a free Master action (place one piece on each of their active cards). This is not implemented in the game loop.

- **Files**: `ProjectL/game_objects.py` — `GameManager.run()`
- **Priority**: Class 2
- **Complexity**: 2

---

## Bugs

### 11. Player.play_turn() logs wrong piece count
Logs `len(self.game_manager.pieces)` which is always `[]`. The actual piece bank is `self.game_manager.piece_bank`.

- **File**: `ProjectL/game_objects.py` — `Player.play_turn()` line 176
- **Priority**: Class 3
- **Complexity**: 1

### 12. Strategy base class raises wrong exception
`Strategy.play_turn()` does `raise NotImplemented` (a built-in constant) instead of `raise NotImplementedError` (an exception).

- **File**: `ProjectL/strategies.py` — `Strategy.play_turn()`
- **Priority**: Class 3
- **Complexity**: 1

### 13. BasicStrat does not remove piece from inventory on placement
`BasicStrat._determine_best_action()` creates `PlacePiece(self.pieces[-1], ...)` but does not pop the piece from the player's list, so the piece remains in inventory after being placed on a card.

- **File**: `ProjectL/strategies.py` — `BasicStrat._determine_best_action()`
- **Priority**: Class 1
- **Complexity**: 1

---

## Summary

| # | Item | Priority | Complexity |
|---|------|----------|------------|
| 5 | No scoring or winner declaration | Class 1 | 1 |
| 13 | BasicStrat does not remove piece on placement | Class 1 | 1 |
| 1 | PlacePiece does not select valid configurations | Class 1 | 2 |
| 2 | TakeCard disconnected from card pool | Class 1 | 2 |
| 3 | UpgradePiece unimplemented | Class 1 | 2 |
| 4 | Master action unimplemented | Class 1 | 2 |
| 7 | No card pool / display mechanism | Class 1 | 2 |
| 6 | Reward piece not granted on card completion | Class 2 | 1 |
| 8 | No piece level restriction on TakePiece | Class 2 | 1 |
| 9 | No proper game-end trigger | Class 2 | 2 |
| 10 | No free Master action at end of turn | Class 2 | 2 |
| 11 | Player.play_turn() logs wrong piece count | Class 3 | 1 |
| 12 | Strategy raises NotImplemented instead of NotImplementedError | Class 3 | 1 |

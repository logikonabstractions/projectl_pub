# Issues: Running BasicStrat vs RandomStrat

## Summary

Running one player with `BasicStrat` and one with `RandomStrat` currently does not work. There are **3 crash bugs** and **3 logic errors**.

| # | File | Line(s) | Type | Description |
|---|------|---------|------|-------------|
| 1 | `strategies.py` | 154 | Crash | `_execute_action()` logging mixes f-string with positional args |
| 2 | `strategies.py` | 226-228 | Crash | `play_turn()` logging mixes f-string with `%d` positional arg |
| 3 | `actions.py` | 107-108 | Crash | `UpgradePiece.__init__` calls `random.choice` on empty list |
| 4 | `strategies.py` | 191 | Logic | `_determine_best_action()` doesn't remove piece from inventory after placement |
| 5 | `strategies.py` | 148-152 | Logic | `_execute_action()` ignores `perform_action()` return value |
| 6 | `actions.py` | 116-120 | Logic | `TakeCard.perform_action()` creates a card from nothing instead of drawing from bank |

---

## Crash Bugs

### 1. `BasicStrat._execute_action()` — logging TypeError (`strategies.py:154`)

```python
self.logger.debug(f"{self.name}  action invalid: {action}", self.name, action.desc, extra={"normal": False, "verbose": True})
```

The format string is an f-string, so `self.name` and `action` are already interpolated into the message. However, `self.name` and `action.desc` are also passed as positional arguments. The `logging` module interprets positional args after the message as `%s`-style format arguments — but there are no `%s` placeholders in the string. This causes a `TypeError` at runtime whenever `BasicStrat` encounters an invalid action.

**Fix:** Remove the extra positional args, or switch to `%s` formatting.

---

### 2. `BasicStrat.play_turn()` — logging TypeError (`strategies.py:226-228`)

```python
self.logger.info(f"{self.player.name} passes remaining %d actions",
               self.name, self.actions_left,
               extra={"normal": True})
```

This mixes an f-string with a `%d` placeholder. The `logging` module will try to substitute `self.name` (a string) into `%d`, which raises a `TypeError`. Even if the types matched, `self.actions_left` would be an unused extra argument. This crashes whenever `BasicStrat` decides to pass its remaining actions.

**Fix:** Use either pure f-string or pure `%`-style formatting, not both.

---

### 3. `UpgradePiece.__init__` — IndexError on empty pieces (`actions.py:107-108`)

```python
if self.piece is None:
    self.piece = random.choice(self.pieces)
```

When no piece is passed to the constructor, it falls back to picking a random piece from `self.pieces`. If the player has no pieces, `random.choice` raises an `IndexError`. `RandomStrat` includes `UpgradePiece` in its action pool, so this crash happens as soon as `RandomStrat` rolls `UpgradePiece` while the player's piece list is empty.

**Fix:** Guard against empty `self.pieces` before calling `random.choice`.

---

## Logic Errors

### 4. Piece not removed from inventory on placement (`strategies.py:191`)

```python
return PlacePiece(self.pieces[-1], self.cards[0], pieces=self.pieces, game_manager=self.player.game_manager)
```

`BasicStrat._determine_best_action()` creates a `PlacePiece` action using `self.pieces[-1]` but never removes that piece from the player's inventory. This means the same piece is "placed" over and over on every turn. Notably, the other code path `_try_place_piece()` (line 169) does call `self.pieces.pop()`, so this is likely an oversight.

**Fix:** Pop the piece from `self.pieces` before or after a successful placement, consistent with `_try_place_piece()`.

---

### 5. `perform_action()` return value ignored (`strategies.py:148-152`)

```python
if action.is_action_valid():
    self.logger.info(f"{self.name}  performs: {action}", extra={"normal": True})
    action.perform_action()
    self.actions_left -= 1
    return True
```

`_execute_action()` checks `is_action_valid()` but then unconditionally decrements `actions_left` and returns `True` regardless of whether `perform_action()` succeeded. For example, `PlacePiece.perform_action()` can return `False` when the randomly chosen configuration doesn't fit the card — but the strategy treats it as a success, consuming the action for nothing.

**Fix:** Check the return value of `perform_action()` and only count the action as spent if it returns `True`.

---

### 6. `TakeCard` creates a card from nothing (`actions.py:116-120`)

```python
def perform_action(self):
    card = Card()
    self.cards.append(card)
```

`TakeCard.perform_action()` instantiates a default `Card()` and appends it to the player's hand. It does not draw from the game's card bank. Compare with `TakePiece.perform_action()` which correctly calls `self.game_manager.get_piece()` to draw from the shared bank. The result is that taken cards are disconnected from the actual game state — the bank doesn't know a card was taken, and the card has no meaningful properties.

**Fix:** Draw from the game manager's card pool, similar to how `TakePiece` works.

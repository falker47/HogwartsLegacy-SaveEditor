# Database Findings & Lock Logic 📚

## Evidence status after the residual audit

The recipes below record historical implementation assumptions, not independent
in-game validation. In particular, the old `WandHandles` and `RevelioPages` mappings
were contradicted by the inspected HL-02B database. Their mutations are now disabled.
See [the evidence audit](nexus-residuals-audit.md) for sources, tests and limitations.

## Historical overview (unverified)
Unlocking "Collections" (Field Guide completion) requires more than just updating the `CollectionDynamic` table. The game performs cross-checks against the `LootItemsDynamic` table to verify that an item was legitimately "looted" or "found".

## The Multi-Table Pattern
To successfully unlock a collection item so it appears in the Field Guide and counts towards challenges, we must perform two operations:

1.  **Update `CollectionDynamic`**
    *   Sets the `ItemState` to `Obtained`.
    *   Updates the `UpdateTime`.
    *   **Purpose**: Updates the UI count in the Field Guide.

2.  **Insert into `LootItemsDynamic`**
    *   Creates a record that the item was "looted".
    *   The `ItemID` often requires a prefix (e.g., `Recipe_Transfiguration_` for Conjurations).
    *   **Purpose**: Validates the item as "owned" prevents re-looting logic issues, and ensures it renders in the specific collection details page.

## Historical mappings (not gameplay-certified)

### 1. Conjurations (Room of Requirement)
*   **CategoryID**: `Conjurations`
*   **Loot Item Prefix**: `Recipe_Transfiguration_` + `ItemID`
*   **SQL Logic**:
    ```sql
    -- 1. Mark as Obtained
    UPDATE CollectionDynamic 
    SET ItemState = 'Obtained', UpdateTime = '-2108045320' 
    WHERE CategoryID = 'Conjurations' AND ItemState <> 'Obtained';

    -- 2. Register as Looted (Crucial for game logic)
    INSERT INTO LootItemsDynamic (ItemID, Looted, ItemRandomWeight, ItemAdjustedWeight, Variation)
    SELECT DISTINCT 
        'Recipe_Transfiguration_' || ItemID, -- Note the prefix
        1, 0, 0, NULL
    FROM CollectionDynamic 
    WHERE CategoryID = 'Conjurations' 
    -- Ensure distinct check to avoid PK violations
    AND ('Recipe_Transfiguration_' || ItemID) NOT IN (SELECT DISTINCT ItemID FROM LootItemsDynamic WHERE ItemID IS NOT NULL);
    ```

### 2. Field Guide / Revelio Pages — disabled

The historical guessed `RevelioPages` category and extra loot writes are not a
supported recipe. Public reader tooling distinguishes lore collections, flying pages
and other page flags in different tables. No page mutation remains enabled here.

### 3. Appearances (Cosmetics)
*   **CategoryID**: `Appearances`
*   **Loot Item Prefix**: None (Direct `ItemID`)
*   **Observation**: Unlocks outfit visuals.

### 4. Wand Handles — disabled

The inspected save uses `WandStyle`, with duplicate obtained/unknown rows and related
usage locks. Merely renaming the old `WandHandles` category does not establish a safe
unlock/revert transition. No replacement SQL recipe is claimed.

### 5. Traits (Gear Upgrades)
*   **CategoryID**: `Traits`
*   **Loot Item Prefix**: None (Direct `ItemID`)
*   **Implementation**: Unlocks the trait in the Collections menu (requires `LootItemsDynamic` to show as found). Note: The *ability* to use traits is handled separately by `LocksDynamic`.

## Future Candidates (Unverified)
*   **Enemies**: Likely just kill counters.
*   **Ingredients / Tools**: Might be standard inventory items.

## Thread Safety Note
All database operations in the UI are now wrapped in thread-safe calls (`self.after` in Python) to prevent `_tkinter.TclError` crashes during lengthy updates or app shutdown.

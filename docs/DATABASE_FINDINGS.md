# Database Findings & Lock Logic 📚

## Overview
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

## Validated Mappings

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

### 2. Field Guide Pages
*   **CategoryID**: `RevelioPages`
*   **Loot Item Prefix**: None (Direct `ItemID`)
*   **Observation**: These are simpler but still benefit from the dual-table update to ensure consistency.

### 3. Appearances (Cosmetics)
*   **CategoryID**: `Appearances`
*   **Loot Item Prefix**: None (Direct `ItemID`)
*   **Observation**: Unlocks outfit visuals.

## Future Candidates (Unverified)
The following categories follow a similar pattern but require verification of their `CategoryID` and potential prefixes:

*   **Wand Handles**: Likely `CategoryID = 'WandHandles'`.
*   **Traits**: Likely `CategoryID = 'Traits'`.
*   **Enemies**: Likely just kill counters, might be in a different table (`AchievementDynamic`?).
*   **Ingredients / Tools**: Might be standard inventory items rather than just collections.

## Thread Safety Note
All database operations in the UI are now wrapped in thread-safe calls (`self.after` in Python) to prevent `_tkinter.TclError` crashes during lengthy updates or app shutdown.

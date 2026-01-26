SELECT CategoryID, COUNT(*) FROM CollectionDynamic GROUP BY CategoryID ORDER BY CategoryID
UPDATE CollectionDynamic SET ItemState = 'Obtained', UpdateTime = '-2108045320' WHERE CategoryID = 'Conjurations' AND ItemState <> 'Obtained'




SELECT * FROM sqlite_master WHERE type='table' AND sql LIKE '%witch%'



SELECT *, 
'Recipe_Transfiguration_' || ItemID AS LootID 
FROM CollectionDynamic 
WHERE CategoryID = 'Conjurations' 
AND LootID NOT IN(SELECT DISTINCT ItemID FROM LootItemsDynamic)
ORDER BY ItemID

WITH LootItems AS
(
SELECT DISTINCT 
'Recipe_Transfiguration_' || ItemID AS LootID 
FROM CollectionDynamic 
WHERE CategoryID = 'Conjurations' 
AND LootID NOT IN(SELECT DISTINCT ItemID FROM LootItemsDynamic)
ORDER BY ItemID
)
INSERT INTO LootItemsDynamic
SELECT 
	LootID AS ITemID,
	true AS Looted,
	0 AS ItemRandomWeight,
	0 AS ItemAdjustedWeight,
	NULL AS Variation
FROM LootItems


SELECT * FROM LootItemsDynamic 
WHERE ItemID LIKE '%Recipe_Transfiguration%' 
AND
ItemID NOT IN (SELECT ItemID FROM gamedb.ItemDefinition WHERE ItemType = 'Recipe_Transfig')


WITH MissingRecipes AS
(
	SELECT * 
	FROM gamedb.ItemDefinition 
	WHERE ItemType='Recipe_Transfig'
	AND ItemID NOT IN (SELECT ItemID FROM InventoryDynamic WHERE HolderID = 'RecipeInventory')
	AND PrerequisiteLockID IS NULL AND PrerequisiteLockID2 IS NULL
),
InsertRecipes AS
(
SELECT 
	((ROW_NUMBER() OVER (ORDER BY ItemID)) + (SELECT MAX(SlotNumber) FROM InventoryDynamic WHERE HolderID = 'RecipeInventory')) AS SlotNumber, 
	* 
	FROM MissingRecipes 
	ORDER BY ItemID
)
INSERT INTO InventoryDynamic
SELECT 
	'Player0' AS CharacterID,
	'RecipeInventory' AS HolderID,
	SlotNumber,
	ItemID,
	NULL AS Variation,
	1 AS Count,
	0 AS Stolen,
	0 AS UniqueItem,
	0 AS KeepOnReset,
	'596332792107260103' AS UpdateTime
FROM InsertRecipes


	INSERT INTO LocksDynamic
	
	SELECT 
	LockID,
	0 AS ELockState
	FROM gamedb.ItemDefinition 
	WHERE ItemType='Recipe_Transfig' AND
	LockID NOT IN (SELECT LockID FROM LocksDynamic)
	
	
	INSERT INTO LocksDynamic
	
	SELECT 
	LockID,
	0 AS ELockState
	FROM gamedb.ItemDefinition 
	WHERE ItemType='Recipe_Transfig' AND
	LockID NOT IN (SELECT LockID FROM LocksDynamic)
	AND PrerequisiteLockID IS NULL AND PrerequisiteLockID2 IS NULL AND LockID NOT LIKE '%Biome%' AND LockID NOT LIKE '%dwiz%'	
	
	
	
-- These seem fine

	SELECT 
	LockID,
	0 AS ELockState
	FROM gamedb.ItemDefinition 
	WHERE ItemType='Recipe_Transfig' AND
	LockID NOT IN (SELECT LockID FROM LocksDynamic)
	AND PrerequisiteLockID IS NULL AND PrerequisiteLockID2 IS NULL AND LockID LIKE '%statue%'	
	
	
	
--Lock Defintion may work too or in tandum.
SELECT * FROM ItemDefinition WHERE ItemID IN (


SELECT RegistryId FROM Registry WHERE SubtypeID = 'TransfigurationUnlock') AND ItemType = 'Recipe_Transfig'	


SELECT
    DISTINCT
    ID.LockID AS LockID
FROM ItemDefinition ID
JOIN Registry R ON R.RegistryID = ID.ItemID AND R.SubtypeID = 'TransfigurationUnlock'
JOIN LockDefinition LD on ID.LockID = LD.LockID
WHERE ID.ItemType='Recipe_Transfig' AND ID.PrerequisiteLockID IS NULL AND PrerequisiteLockID2 IS NULL;


WITH ValidLockItems AS
(
SELECT
    DISTINCT
    ID.LockID AS LockID
FROM gamedb.ItemDefinition ID
JOIN gamedb.Registry R ON R.RegistryID = ID.ItemID AND R.SubtypeID = 'TransfigurationUnlock'
JOIN gamedb.LockDefinition LD on ID.LockID = LD.LockID
WHERE ID.ItemType='Recipe_Transfig' AND ID.PrerequisiteLockID IS NULL AND PrerequisiteLockID2 IS NULL
)
--INSERT INTO LocksDynamic
SELECT LockID, 0 AS ELockState
FROM ValidLockItems WHERE LockID NOT IN (SELECT LockID FROM LocksDynamic)


WITH ValidLockItems AS
(
SELECT DISTINCT LD.LockID FROM FastTravelLocations FTL
JOIN LockDefinition LD ON LD.LockID = FTL.Name
WHERE FTL.ShowOnMap = 1
)
--INSERT INTO LocksDynamic
SELECT LockID, 0 AS ELockState
FROM ValidLockItems WHERE LockID NOT IN (SELECT LockID FROM LocksDynamic)
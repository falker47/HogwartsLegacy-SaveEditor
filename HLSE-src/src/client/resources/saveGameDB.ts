// @ts-ignore
import sqlJSWasmURL from 'sql.js/dist/sql-wasm.wasm?url';
import initSqlJs, { Database } from 'sql.js';

import { GearItem, LockListItem, LockState, PlayerData, PlayerResource } from '../interfaces';

interface LockItem {
    LockID: string;
    ELockState: number;
}

export class SaveGameDB {
    #gameDBBytes: Uint8Array;
    #gameDB: Promise<Database>;

    constructor(gameDB: Uint8Array) {
        this.#gameDBBytes = gameDB;
        this.#gameDB = this.#initDB();
    }

    async #initDB(): Promise<Database> {
        const SQL = await initSqlJs({
            locateFile: () => sqlJSWasmURL
        });

        return new SQL.Database(this.#gameDBBytes);
    }

    #mapSqlResults<T>(sqlResults: initSqlJs.QueryExecResult, columnExtractList: string[] = []): T[] {
        if (!sqlResults) {
            return [];
        }
        const columns = sqlResults.columns;
        const rows = sqlResults.values;

        let extractList: (string | null)[] = [];

        if (columnExtractList.length > 0) {
            for (const columnName of columns) {
                if (columnExtractList.includes(columnName)) {
                    extractList.push(columnName);
                }
                else {
                    extractList.push(null);
                }
            }
        }
        else {
            extractList = columns;
        }

        return rows.map((rowData) => {
            const result = {};

            for (let i = 0; i < extractList.length; i++) {
                const propertyName = extractList[i];
                if (propertyName !== null) {
                    result[propertyName] = rowData[i];
                }
            }
            return result;
        }) as T[];
    }

    async getPlayerResources(): Promise<PlayerResource[]> {
        const db = await this.#gameDB;
        const inventoryList = db.exec(`SELECT * FROM 'InventoryDynamic'`
            + ` WHERE CharacterID = 'Player0' AND`
            + ` HolderID = 'ResourceInventory' OR HolderID = 'HealthPotionStorage'`
            + ` ORDER BY HolderID, SlotNumber`);
        return this.#mapSqlResults<PlayerResource>(inventoryList[0], ['SlotNumber', 'ItemID', 'Count', 'HolderID']);
    }

    async modifyPlayerResource(playerResource: PlayerResource): Promise<void> {
        const db = await this.#gameDB;

        db.exec(
            `UPDATE InventoryDynamic`
            + ` SET Count = $count`
            + ` WHERE ItemID = $itemID`
            + ` AND HolderID = $holderID`
            + ` AND SlotNumber = $slotNumber;`,
            {
                $count: playerResource.Count,
                $itemID: playerResource.ItemID,
                $holderID: playerResource.HolderID,
                $slotNumber: playerResource.SlotNumber
            }
        );
    }

    async getPlayerCombatResources(): Promise<PlayerResource[]> {
        const db = await this.#gameDB;
        const inventoryList = db.exec(`SELECT * FROM 'InventoryDynamic'`
            + ` WHERE CharacterID = 'Player0' AND`
            + ` HolderID = 'SanctuaryWheel' AND`
            + ` ItemID IS NOT NULL`
            + ` ORDER BY SlotNumber`);
        return this.#mapSqlResults<PlayerResource>(inventoryList[0], ['SlotNumber', 'ItemID', 'Count', 'HolderID']);
    }

    async getPlayerMissionResources(): Promise<PlayerResource[]> {
        const db = await this.#gameDB;
        const inventoryList = db.exec(`SELECT * FROM 'InventoryDynamic'`
            + ` WHERE CharacterID = 'Player0' AND`
            + ` HolderID = 'MissionItems' AND`
            + ` ItemID IS NOT NULL`
            + ` ORDER BY SlotNumber`);
        return this.#mapSqlResults<PlayerResource>(inventoryList[0], ['SlotNumber', 'ItemID', 'Count', 'HolderID']);
    }

    async getPlayerPerks(): Promise<string[]> {
        const db = await this.#gameDB;
        const perkList = db.exec(`SELECT PerkID FROM PerkDynamic ORDER BY PerkID`);
        if (perkList.length === 0) {
            return [];
        }
        return perkList[0].values.map((sqlValue) => {
            return sqlValue[0] as string;
        });
    }

    async deletePlayerPerk(perkName: string): Promise<void> {
        const db = await this.#gameDB;
        db.exec(`DELETE FROM PerkDynamic WHERE PerkID = $perkName`, {
            $perkName: perkName
        });
    }

    async getPlayerData(): Promise<PlayerData> {
        const db = await this.#gameDB;

        // Helper function to safely extract value from query result
        const safeExtract = (result: any[], defaultValue = ''): string => {
            try {
                if (result && result.length > 0 && result[0].values && result[0].values.length > 0) {
                    return (result[0].values[0][0] as string) ?? defaultValue;
                }
            } catch (e) {
                console.warn('Failed to extract value:', e);
            }
            return defaultValue;
        };

        const firstNameData = db.exec(`SELECT DataValue FROM MiscDataDynamic WHERE DataName = 'PlayerFirstName'`);
        const lastNameData = db.exec(`SELECT DataValue FROM MiscDataDynamic WHERE DataName = 'PlayerLastName'`);
        const houseData = db.exec(`SELECT DataValue FROM MiscDataDynamic WHERE DataName = 'HouseID'`);
        const expData = db.exec(`SELECT DataValue FROM MiscDataDynamic WHERE DataName = 'ExperiencePoints'`);
        const levelData = db.exec(`SELECT DataValue FROM MiscDataDynamic WHERE DataName = 'LevelUpMult'`);
        const perkData = db.exec(`SELECT DataValue FROM MiscDataDynamic WHERE DataName = 'PerkPoints'`);
        const baseInvCap = db.exec(`SELECT DataValue FROM MiscDataDynamic WHERE DataName = 'BaseInventoryCapacity'`);

        return {
            FirstName: safeExtract(firstNameData),
            LastName: safeExtract(lastNameData),
            House: safeExtract(houseData),
            Exp: safeExtract(expData, '0'),
            Level: safeExtract(levelData, '0'),
            PerkPoints: safeExtract(perkData, '0'),
            BaseInventoryCapacity: safeExtract(baseInvCap, '20')
        };
    }

    async modifyPlayerName(playerData: PlayerData): Promise<void> {
        const db = await this.#gameDB;
        db.exec(`UPDATE MiscDataDynamic SET DataValue = $firstName WHERE DataName = 'PlayerFirstName'`, {
            $firstName: playerData.FirstName
        });
        db.exec(`UPDATE MiscDataDynamic SET DataValue = $lastName WHERE DataName = 'PlayerLastName'`, {
            $lastName: playerData.LastName
        });
    }

    async addHouseFlooLocations(): Promise<void> {
        const db = await this.#gameDB;
        db.exec(`WITH FlooLocations AS\n(\n\tSELECT \n\t'FT_HW_GryffindorCommonRoom' AS FlooLocation\n\tUNION \n\tSELECT \n\t'FT_HW_HufflepuffCommonRoom' AS FlooLocation\n\tUNION \n\tSELECT \n\t'FT_HW_RavenclawCommonRoom' AS FlooLocation\n\tUNION \n\tSELECT \n\t'FT_HW_SlytherinCommonRoom' AS FlooLocation\n)\nINSERT INTO LocksDynamic\nSELECT \n\tFlooLocation AS LockID,\n\t0 AS ELockState\nFROM FlooLocations WHERE FlooLocation NOT IN (SELECT LockID FROM LocksDynamic)`);
    }

    async modifyPlayerHouse(playerData: PlayerData): Promise<void> {
        const db = await this.#gameDB;
        db.exec(`UPDATE MiscDataDynamic SET DataValue = $houseName WHERE DataName = 'HouseID'`, {
            $houseName: playerData.House
        });
        await this.addHouseFlooLocations();
    }

    async modifyPlayerExp(newExp: string): Promise<void> {
        const db = await this.#gameDB;
        db.exec(`UPDATE MiscDataDynamic SET DataValue = $newExp WHERE DataName = 'ExperiencePoints'`, {
            $newExp: newExp
        });
    }

    async modifyPlayerPerkPoints(newPerkPoints: string): Promise<void> {
        const db = await this.#gameDB;
        db.exec(`UPDATE MiscDataDynamic SET DataValue = $newPerkPoints WHERE DataName = 'PerkPoints'`, {
            $newPerkPoints: newPerkPoints
        });
    }

    async modifyPlayerInventoryCapacity(newInvCap: string): Promise<void> {
        const db = await this.#gameDB;
        db.exec(`UPDATE MiscDataDynamic SET DataValue = $newInvCap WHERE DataName = 'BaseInventoryCapacity'`, {
            $newInvCap: newInvCap
        });
    }

    async getDBBytes(): Promise<Uint8Array> {
        const db = await this.#gameDB;
        return db.export();
    }

    async insertUpdateMapItem(mapLocationID, mapState = 9): Promise<void> {
        const db = await this.#gameDB;
        const mapItem = db.exec('SELECT State FROM MapLocationDataDynamic WHERE MapLocationID = ?', [mapLocationID]);
        if (mapItem.length === 0) {
            db.exec('INSERT INTO MapLocationDataDynamic (MapLocationID, State) VALUES (?,?)', [mapLocationID, mapState]);
        }
        else {
            db.exec('UPDATE MapLocationDataDynamic SET State = ? WHERE MapLocationID = ?', [mapState, mapLocationID]);
        }
    }

    async insertLockItem(lockItemID: string, lockState: number): Promise<void> {
        const db = await this.#gameDB;
        const lockExists = db.exec('SELECT LockID FROM LocksDynamic WHERE LockID = ?', [lockItemID]);
        if (lockExists.length === 0) {
            db.exec('INSERT INTO LocksDynamic (LockID, ELockState) VALUES (?,?)', [lockItemID, lockState]);
        }
    }

    async insertUpdateLockItem(lockItemID: string, lockState: number): Promise<void> {
        const db = await this.#gameDB;
        const lockExists = db.exec('SELECT LockID FROM LocksDynamic WHERE LockID = ?', [lockItemID]);
        if (lockExists.length === 0) {
            db.exec('INSERT INTO LocksDynamic (LockID, ELockState) VALUES (?,?)', [lockItemID, lockState]);
        }
        else {
            db.exec('UPDATE LocksDynamic SET ELockState = ? WHERE LockID = ?', [lockState, lockItemID]);
        }
    }

    async updateLockState(lockItem: LockState, delForDisable = true): Promise<void> {
        const db = await this.#gameDB;
        if (lockItem.LockValue === '1' && delForDisable) {
            db.exec('DELETE FROM LocksDynamic WHERE LockID = ?', [lockItem.LockID]);
        }
        else {
            await this.insertUpdateLockItem(lockItem.LockID, parseInt(lockItem.LockValue));
        }
    }

    async getLockItems(): Promise<LockItem[]> {
        const db = await this.#gameDB;
        const lockItems = db.exec('SELECT * FROM LocksDynamic');
        return this.#mapSqlResults<LockItem>(lockItems[0], ['LockID', 'ELockState']);
    }

    async getLockStates(filter: LockListItem[]): Promise<LockState[]> {
        const lockList = await this.getLockItems();
        const lockListMap = filter.map<LockState>((lock) => {
            const foundLockItem = lockList.find((lockItem) => lockItem.LockID === lock.LockID);
            if (foundLockItem) {
                return {
                    LockID: lock.LockID,
                    LockValue: foundLockItem.ELockState.toString(),
                    RecordExists: true
                };
            }
            else {
                return {
                    LockID: lock.LockID,
                    LockValue: '1',
                    RecordExists: false
                };
            }
        });
        lockListMap.sort((a, b) => {
            const nameA = a.LockID.toUpperCase(); // ignore upper and lowercase
            const nameB = b.LockID.toUpperCase(); // ignore upper and lowercase
            if (nameA < nameB) {
                return -1;
            }
            if (nameA > nameB) {
                return 1;
            }

            // names must be equal
            return 0;
        });
        return lockListMap;
    }

    async getPlayerGearInventory(): Promise<GearItem[]> {
        const db = await this.#gameDB;
        const inventoryList = db.exec(`SELECT GD.* FROM InventoryDynamic ID `
            + ` JOIN GearItemsDynamic GD ON GD.GearVariation = ID.Variation`
            + ` WHERE  ID.CharacterID = 'Player0'`
            + ` AND ID.HolderID = 'ActorBackpack'`
            + ` AND ID.ItemID IS NOT NULL`
            + ` AND ID.Variation IS NOT NULL`);
        return this.#mapSqlResults<GearItem>(inventoryList[0], []);
    }

    async updateGearItem(item: GearItem): Promise<void> {
        const db = await this.#gameDB;
        db.exec(
            `UPDATE GearItemsDynamic`
            + ` SET OffenseStat = $offenseStat, DefenseStat = $defenseStat`
            + ` WHERE GearVariation = $gearVariation;`,
            {
                $gearVariation: item.GearVariation,
                $offenseStat: item.OffenseStat,
                $defenseStat: item.DefenseStat
            }
        );
    }
}

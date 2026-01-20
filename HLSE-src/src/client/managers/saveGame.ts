import AppStateRA from '../resources/appState';
import { GearItem, LockState, PlayerData, PlayerResource } from '../interfaces';
import { FastTravelLocks, TransFigurationLocks, SpellLocks, GearLocks, TraitLocks } from '../resources/lists';

class SaveGameManager
{
    async getPlayerResourceInventory() : Promise<PlayerResource[]>
    {
        if(!AppStateRA.saveGameDB)
        {
            return [];
        }

        return AppStateRA.saveGameDB.getPlayerResources();
    }

    async getPlayerCombatResourceInventory() : Promise<PlayerResource[]>
    {
        if(!AppStateRA.saveGameDB)
        {
            return [];
        }

        return AppStateRA.saveGameDB.getPlayerCombatResources();
    }

    async getPlayerMissionResources() : Promise<PlayerResource[]>
    {
        if(!AppStateRA.saveGameDB)
        {
            return [];
        }

        return AppStateRA.saveGameDB.getPlayerMissionResources();
    }

    async getPlayerPerks() : Promise<string[]>
    {
        if(!AppStateRA.saveGameDB)
        {
            return [];
        }

        return AppStateRA.saveGameDB.getPlayerPerks();
    }

    async deletePerk(perkName : string) : Promise<void>
    {
        if(!AppStateRA.saveGameDB)
        {
            return;
        }

        return AppStateRA.saveGameDB.deletePlayerPerk(perkName);
    }

    async modifyPlayerData(playerData : PlayerData) : Promise<void>
    {
        if(!AppStateRA.saveGameDB)
        {
            return;
        }

        await AppStateRA.saveGameDB.modifyPlayerName(playerData);
        await AppStateRA.saveGameDB.modifyPlayerHouse(playerData);
        await AppStateRA.saveGameDB.modifyPlayerPerkPoints(playerData.PerkPoints);
        await AppStateRA.saveGameDB.modifyPlayerInventoryCapacity(playerData.BaseInventoryCapacity);
        await AppStateRA.saveGameDB.modifyPlayerExp(playerData.Exp);
    }

    async modifyPlayerResource(playerResource : PlayerResource) : Promise<void>
    {
        if(!AppStateRA.saveGameDB)
        {
            return;
        }

        return AppStateRA.saveGameDB.modifyPlayerResource(playerResource);
    }

    async getPlayerData() : Promise<PlayerData>
    {
        if(!AppStateRA.saveGameDB)
        {
            return {
                FirstName: '',
                LastName: '',
                House: '',
                Exp: '',
                Level: '',
                PerkPoints: '',
                BaseInventoryCapacity: ''
            };
        }

        return AppStateRA.saveGameDB.getPlayerData();
    }

    getDatabase(secondary = false) : Uint8Array
    {
        if(!AppStateRA.saveGameData)
        {
            return new Uint8Array(0);
        }
        if(secondary)
        {
            return AppStateRA.saveGameData.secondaryDB;
        }
        return AppStateRA.saveGameData.primaryDB;
    }

    async generateSaveFile(db1 : Uint8Array | null = null, db2 : Uint8Array | null = null) : Promise<Uint8Array>
    {
        if(!AppStateRA.saveGameData || !AppStateRA.saveGameDB)
        {
            return new Uint8Array(0);
        }

        db1 = db1 ? db1 : await AppStateRA.saveGameDB.getDBBytes();
        db2 = db2 ? db2 : AppStateRA.saveGameData.secondaryDB;

        return AppStateRA.saveGameData.generateSaveFile(db1, db2);
    }

    async unlockFastTravelPoints() : Promise<void>
    {
        if(!AppStateRA.saveGameData || !AppStateRA.saveGameDB)
        {
            return;
        }
        for(const lockItem of FastTravelLocks)
        {
            // eslint-disable-next-line no-await-in-loop
            await AppStateRA.saveGameDB.insertLockItem(lockItem.LockID, 0);
            // eslint-disable-next-line no-await-in-loop
            await AppStateRA.saveGameDB.insertUpdateMapItem(lockItem.LockID);
        }
    }

    async unlockTransfigurationItems() : Promise<void>
    {
        if(!AppStateRA.saveGameData || !AppStateRA.saveGameDB)
        {
            return;
        }
        for(const lockItem of TransFigurationLocks)
        {
            // eslint-disable-next-line no-await-in-loop
            await AppStateRA.saveGameDB.insertLockItem(lockItem.LockID, 0);
        }
    }

    async unlockSpells() : Promise<void>
    {
        if(!AppStateRA.saveGameData || !AppStateRA.saveGameDB)
        {
            return;
        }
        for(const lockItem of SpellLocks)
        {
            // eslint-disable-next-line no-await-in-loop
            await AppStateRA.saveGameDB.insertLockItem(lockItem.LockID, 0);
        }
    }

    async unlockGear() : Promise<void>
    {
        if(!AppStateRA.saveGameData || !AppStateRA.saveGameDB)
        {
            return;
        }
        for(const lockItem of GearLocks)
        {
            // eslint-disable-next-line no-await-in-loop
            await AppStateRA.saveGameDB.insertLockItem(lockItem.LockID, 0);
        }
    }

    async unlockTraits() : Promise<void>
    {
        if(!AppStateRA.saveGameData || !AppStateRA.saveGameDB)
        {
            return;
        }
        for(const lockItem of TraitLocks)
        {
            // eslint-disable-next-line no-await-in-loop
            await AppStateRA.saveGameDB.insertLockItem(lockItem.LockID, 0);
        }
    }

    async getPlayerGearInventory() : Promise<GearItem[]>
    {
        if(!AppStateRA.saveGameData || !AppStateRA.saveGameDB)
        {
            return [];
        }
        return AppStateRA.saveGameDB.getPlayerGearInventory();
    }

    async updateGearItem(item : GearItem) : Promise<void>
    {
        if(!AppStateRA.saveGameData || !AppStateRA.saveGameDB)
        {
            return;
        }
        return AppStateRA.saveGameDB.updateGearItem(item);
    }

    async getSpellLocks() : Promise<LockState[]>
    {
        if(!AppStateRA.saveGameData || !AppStateRA.saveGameDB)
        {
            return [];
        }
        return AppStateRA.saveGameDB.getLockStates(SpellLocks);
    }

    async getFastTravelLocks() : Promise<LockState[]>
    {
        if(!AppStateRA.saveGameData || !AppStateRA.saveGameDB)
        {
            return [];
        }
        return AppStateRA.saveGameDB.getLockStates(FastTravelLocks);
    }

    async getGearLocks() : Promise<LockState[]>
    {
        if(!AppStateRA.saveGameData || !AppStateRA.saveGameDB)
        {
            return [];
        }
        return AppStateRA.saveGameDB.getLockStates(GearLocks);
    }

    async getTraitLocks() : Promise<LockState[]>
    {
        if(!AppStateRA.saveGameData || !AppStateRA.saveGameDB)
        {
            return [];
        }
        return AppStateRA.saveGameDB.getLockStates(TraitLocks);
    }

    async getTransfigurationLocks() : Promise<LockState[]>
    {
        if(!AppStateRA.saveGameData || !AppStateRA.saveGameDB)
        {
            return [];
        }
        return AppStateRA.saveGameDB.getLockStates(TransFigurationLocks);
    }

    async updateLockState(lockItem : LockState) : Promise<void>
    {
        if(!AppStateRA.saveGameData || !AppStateRA.saveGameDB)
        {
            return;
        }
        return AppStateRA.saveGameDB.updateLockState(lockItem);
    }

    async updateLockStateMap(lockItem : LockState) : Promise<void>
    {
        if(!AppStateRA.saveGameData || !AppStateRA.saveGameDB)
        {
            return;
        }
        await AppStateRA.saveGameDB.updateLockState(lockItem);
        await AppStateRA.saveGameDB.insertUpdateMapItem(
            lockItem.LockID,
            lockItem.LockValue === '1' ? 8 : 9
        );
    }
}

export default new SaveGameManager();

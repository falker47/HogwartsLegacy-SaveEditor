import { reactive } from 'vue';

import { AppState } from '../interfaces/appState';
import { SaveGameData } from '../lib/saveGameData';
import { SaveGameDB } from './saveGameDB';

class AppStateRA
{
    #appState : AppState;
    #saveGameData : SaveGameData | undefined;
    #saveGameDB : SaveGameDB | undefined;

    constructor()
    {
        this.#appState = {
            isSaveFileLoaded: false
        };
    }

    get appState() : AppState
    {
        return reactive(this.#appState);
    }

    get saveGameData() : SaveGameData | undefined
    {
        return this.#saveGameData;
    }

    get saveGameDB() : SaveGameDB | undefined
    {
        return this.#saveGameDB;
    }

    async loadSaveGameData(fileArrayBuffer : ArrayBuffer) : Promise<void>
    {
        this.#saveGameData = undefined;
        this.#saveGameDB = undefined;
        this.appState.isSaveFileLoaded = false;
        try
        {
            this.#saveGameData = new SaveGameData(fileArrayBuffer);
            this.#saveGameDB = new SaveGameDB(this.#saveGameData.primaryDB.slice());
            this.appState.isSaveFileLoaded = true;
        }
        catch (err)
        {
            console.error('Error Loading Save Game Data');
            console.error(err);
        }
    }
}

export default new AppStateRA();

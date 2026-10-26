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
        const data = new SaveGameData(fileArrayBuffer);
        const database = new SaveGameDB(data.primaryDB.slice());
        // Finish SQLite initialization before replacing the editable session.
        // A rejected replacement must preserve the user's pending changes.
        await database.getDBBytes();
        this.#saveGameData = data;
        this.#saveGameDB = database;
        this.appState.isSaveFileLoaded = true;
    }
}

export default new AppStateRA();

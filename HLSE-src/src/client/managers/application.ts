import AppStateRA from '../resources/appState';
import { AppState } from '../interfaces/appState';

class ApplicationManager
{
    get appState() : AppState
    {
        return AppStateRA.appState;
    }

    async loadSaveGameData(fileArrayBuffer : ArrayBuffer) : Promise<void>
    {
        await AppStateRA.loadSaveGameData(fileArrayBuffer);
    }

    getModifiedSaveData() : Uint8Array | null
    {
        if(!AppStateRA.saveGameData)
        {
            console.log('No save data oaded');
            return null;
        }

        return AppStateRA.saveGameData.generateSaveFile(AppStateRA.saveGameData.primaryDB);
    }
}

export default new ApplicationManager();

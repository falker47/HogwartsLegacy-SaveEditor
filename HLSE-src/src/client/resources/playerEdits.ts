import { PlayerData } from '../interfaces';

export const progressionWarning = 'Experience and Talent Points are read-only. This editor cannot verify talent unlock prerequisites or repair progression changed before talents unlock.';

export function playerChanges(current : PlayerData, original : PlayerData) : Partial<PlayerData>
{
    const changes : Partial<PlayerData> = {};
    for(const key of Object.keys(current) as (keyof PlayerData)[])
    {
        if(current[key] !== original[key])
        {
            changes[key] = current[key];
        }
    }
    return changes;
}

export function validatePlayerNumber(value : string, label : string) : void
{
    // Storage bound only; this does not certify a valid gameplay state.
    if(typeof value !== 'string' || !/^\d+$/.test(value)
        || !Number.isSafeInteger(Number(value)) || Number(value) > 2147483647)
    {
        throw new Error(`${ label } must be a whole number from 0 to 2147483647.`);
    }
}

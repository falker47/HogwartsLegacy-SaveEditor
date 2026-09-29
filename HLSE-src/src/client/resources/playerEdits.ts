import { PlayerData } from '../interfaces';

export const MAX_VANILLA_EXP = 74000;
export const MAX_VANILLA_TALENT_POINTS = 36;

const LEVEL_THRESHOLDS = [
    0, 500, 1030, 1595, 2195, 2835, 3515, 4240, 5015, 5840,
    6715, 7650, 8650, 9700, 10825, 12025, 13300, 14660, 16110, 17650,
    19290, 21035, 22885, 24865, 26965, 29205, 31590, 34130, 36830, 39710,
    42750, 46000, 49500, 53000, 56500, 60000, 63500, 67000, 70500, 74000
];

export const progressionWarning =
    'Experience and Talent Points are editable with safeguards. XP is limited to 0–74000; '
    + 'level decreases are blocked, and level jumps are blocked until this save shows evidence '
    + 'that the Talent system has been initialized. Unspent Talent Points plus learned talents '
    + 'cannot exceed the vanilla lifetime maximum of 36. Keep a backup before progression edits.';

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

export function validatePlayerNumber(value : string, label : string, max = 2147483647) : void
{
    if(typeof value !== 'string' || !/^\d+$/.test(value)
        || !Number.isSafeInteger(Number(value)) || Number(value) > max)
    {
        throw new Error(`${ label } must be a whole number from 0 to ${ max }.`);
    }
}

export function levelForExperience(exp : number) : number
{
    let level = 1;
    for(let i = 0; i < LEVEL_THRESHOLDS.length; i++)
    {
        if(exp >= LEVEL_THRESHOLDS[i])
        {
            level = i + 1;
        }
        else
        {
            break;
        }
    }
    return Math.min(level, 40);
}

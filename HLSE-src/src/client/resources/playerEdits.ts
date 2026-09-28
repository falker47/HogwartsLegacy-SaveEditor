import { PlayerData } from '../interfaces';

export const EXPERIENCE_LEVEL_THRESHOLDS = [
    0, 500, 1030, 1595, 2195, 2835, 3515, 4240, 5015, 5840,
    6715, 7650, 8650, 9700, 10825, 12025, 13300, 14660, 16110, 17650,
    19290, 21035, 22885, 24865, 26965, 29205, 31590, 34130, 36830, 39710,
    42750, 46000, 49500, 53000, 56500, 60000, 63500, 67000, 70500, 74000
] as const;

export const MAX_EXPERIENCE = 74000;
export const MAX_TALENT_POINTS = 36;

export interface ProgressionContext
{
    experience : number;
    level : number;
    unspentTalentPoints : number;
    spentTalentPoints : number;
    talentSystemUnlocked : boolean;
}

export interface ProgressionEditOptions
{
    advancedTalentPoints?: boolean;
}

export const progressionWarning =
    'Progression edits are explicit only. Experience can be increased up to level 40. '
    + 'Talent Points require the in-game talent menu to be unlocked. Safe mode keeps '
    + 'spent + unspent points within the amount earned for the resulting level; Advanced '
    + 'Talent Points may use the lifetime pool early, but never beyond 36 total points.';

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

export function validatePlayerNumber(value : string, label : string, max = 2147483647) : number
{
    if(typeof value !== 'string' || !/^\d+$/.test(value)
        || !Number.isSafeInteger(Number(value)) || Number(value) > max)
    {
        throw new Error(`${ label } must be a whole number from 0 to ${ max }.`);
    }
    return Number(value);
}

export function levelFromExperience(experience : number) : number
{
    let level = 1;
    for(let index = 0; index < EXPERIENCE_LEVEL_THRESHOLDS.length; index += 1)
    {
        if(experience >= EXPERIENCE_LEVEL_THRESHOLDS[index])
        {
            level = index + 1;
        }
        else
        {
            break;
        }
    }
    return level;
}

export function earnedTalentPoints(level : number) : number
{
    return Math.max(0, Math.min(MAX_TALENT_POINTS, level - 4));
}

export function validateProgressionChanges(
    changes : Partial<PlayerData>,
    context : ProgressionContext,
    options : ProgressionEditOptions = {}
) : void
{
    const changesExperience = Object.prototype.hasOwnProperty.call(changes, 'Exp');
    const changesTalentPoints = Object.prototype.hasOwnProperty.call(changes, 'PerkPoints');
    if(!changesExperience && !changesTalentPoints)
    {
        return;
    }

    if(!context.talentSystemUnlocked)
    {
        throw new Error(
            'Progression editing is disabled until the in-game Talent menu is unlocked '
            + '(complete Jackdaw\'s Rest / reach the normal talent unlock).'
        );
    }

    const proposedExperience = changesExperience
        ? validatePlayerNumber(changes.Exp as string, 'Experience', MAX_EXPERIENCE)
        : context.experience;

    if(proposedExperience < context.experience && context.experience <= MAX_EXPERIENCE)
    {
        throw new Error(
            'Experience can only be increased. Lowering XP can invalidate learned talents '
            + 'and story/progression state.'
        );
    }

    const proposedUnspent = changesTalentPoints
        ? validatePlayerNumber(changes.PerkPoints as string, 'Talent Points', MAX_TALENT_POINTS)
        : context.unspentTalentPoints;

    if(context.spentTalentPoints > MAX_TALENT_POINTS)
    {
        throw new Error('This save already contains more than 36 learned talents; progression editing is blocked.');
    }

    const lifetimeRemaining = MAX_TALENT_POINTS - context.spentTalentPoints;
    if(proposedUnspent > lifetimeRemaining)
    {
        throw new Error(
            `Talent Points would exceed the 36-point lifetime pool: `
            + `${ context.spentTalentPoints } learned + ${ proposedUnspent } unspent > 36.`
        );
    }

    if(!options.advancedTalentPoints)
    {
        const resultingLevel = levelFromExperience(proposedExperience);
        const safeRemaining = Math.max(0, earnedTalentPoints(resultingLevel) - context.spentTalentPoints);
        if(proposedUnspent > safeRemaining)
        {
            throw new Error(
                `Safe Talent Points limit at level ${ resultingLevel } is ${ safeRemaining } unspent `
                + `with ${ context.spentTalentPoints } talents already learned. `
                + 'Enable Advanced Talent Points only if you intentionally want to use future lifetime points early.'
            );
        }
    }
}

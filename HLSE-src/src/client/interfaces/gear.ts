export interface GearItem
{
    SlotNumber : number;
    GearID : string;
    GearVariation : string;
    GearLevel : number;
    OffenseStat : number | string;
    DefenseStat : number | string;
    CooldownStat : number;
    GeneralAbility1 : string;
    GeneralAbility2 : string;
    GeneralAbility3 : string;
    GearAppearanceOverrideID : string;
    IsIdentified : number;
    StatUpgrades : number;
    GearTags : string;
}

// Select the inventory location and immutable gear key; only these two stats are writable.
export interface GearStatEdit
{
    GearID : string;
    GearVariation : string;
    SlotNumber : number;
    OffenseStat ?: number | string;
    DefenseStat ?: number | string;
}

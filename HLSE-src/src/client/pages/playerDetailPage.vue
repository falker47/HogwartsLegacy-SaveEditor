<script setup lang="ts">
import { ref, onBeforeMount, computed } from 'vue';
import SaveGameManager from '../managers/saveGame';
import { PlayerData } from '../interfaces';
import {
  ProgressionContext,
  earnedTalentPoints,
  levelFromExperience,
  playerChanges,
  progressionWarning
} from '../resources/playerEdits';

const playerData = ref<PlayerData>({} as PlayerData);
const originalData = ref<PlayerData>({} as PlayerData);
const progression = ref<ProgressionContext | null>(null);
const advancedTalentPoints = ref(false);
const ready = ref(false);
const errorMessage = ref('');
const playerDataChanged = computed(() => ready.value
  && Object.keys(playerChanges(playerData.value, originalData.value)).length > 0);
const progressionUnlocked = computed(() => progression.value?.talentSystemUnlocked === true);
const resultingLevel = computed(() => {
  const value = Number(playerData.value.Exp);
  return Number.isSafeInteger(value) && value >= 0 ? levelFromExperience(value) : 1;
});
const safeUnspentLimit = computed(() => {
  if(!progression.value)
  {
    return 0;
  }
  return Math.max(0, earnedTalentPoints(resultingLevel.value) - progression.value.spentTalentPoints);
});
const lifetimeUnspentLimit = computed(() => {
  if(!progression.value)
  {
    return 0;
  }
  return Math.max(0, 36 - progression.value.spentTalentPoints);
});
const progressionStatus = computed(() => {
  if(!progression.value)
  {
    return '';
  }
  if(!progression.value.talentSystemUnlocked)
  {
    return 'Talent menu not unlocked: Experience and Talent Points editing stays disabled until normal story unlock.';
  }
  return `Resulting level ${ resultingLevel.value } · learned talents ${ progression.value.spentTalentPoints }/36 · `
    + `safe unspent limit ${ safeUnspentLimit.value } · lifetime remaining ${ lifetimeUnspentLimit.value }.`;
});

async function refreshData()
{
  ready.value = false;
  try
  {
    const [ data, progressionData ] = await Promise.all([
      SaveGameManager.getPlayerData(),
      SaveGameManager.getProgressionContext()
    ]);
    playerData.value = { ...data };
    originalData.value = { ...data };
    progression.value = progressionData;
    advancedTalentPoints.value = false;
    errorMessage.value = '';
    ready.value = true;
  }
  catch (error)
  {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  }
}

async function resetPlayerData()
{
  await refreshData();
}

async function savePlayerData()
{
  if(!ready.value)
  {
    return;
  }
  try
  {
    await SaveGameManager.modifyPlayerData(
      playerChanges(playerData.value, originalData.value),
      { advancedTalentPoints: advancedTalentPoints.value }
    );
    await refreshData();
  }
  catch (error)
  {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  }
}

onBeforeMount(refreshData);
</script>

<template>
  <div class="d-flex flex-column ma-5">
    <v-card density="compact">
      <v-container>
        <v-alert
          type="info"
          variant="tonal"
          class="mb-4"
        >
          {{ progressionWarning }}
        </v-alert>
        <v-alert
          v-if="progressionStatus"
          :type="progressionUnlocked ? 'info' : 'warning'"
          variant="tonal"
          class="mb-4"
        >
          {{ progressionStatus }}
        </v-alert>
        <v-alert
          v-if="errorMessage"
          type="error"
          class="mb-4"
        >
          {{ errorMessage }}
        </v-alert>

        <v-row>
          <v-col cols="4">
            <v-text-field
              v-model="playerData.FirstName"
              label="First Name"
              variant="underlined"
            />
          </v-col>
          <v-col cols="4">
            <v-text-field
              v-model="playerData.LastName"
              label="Last Name"
              variant="underlined"
            />
          </v-col>
          <v-col cols="4">
            <v-combobox
              v-model="playerData.House"
              label="House"
              :items="['Gryffindor', 'Hufflepuff', 'Ravenclaw', 'Slytherin', 'Unaffiliated']"
              variant="underlined"
            />
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="4">
            <v-text-field
              v-model="playerData.Exp"
              :readonly="!progressionUnlocked"
              min="0"
              max="74000"
              step="1"
              type="number"
              label="Experience"
              hint="Increase only; 74,000 is level 40."
              persistent-hint
              variant="underlined"
            />
          </v-col>
          <v-col cols="4">
            <v-text-field
              v-model="playerData.PerkPoints"
              :readonly="!progressionUnlocked"
              min="0"
              :max="advancedTalentPoints ? lifetimeUnspentLimit : safeUnspentLimit"
              step="1"
              type="number"
              label="Talent Points"
              :hint="advancedTalentPoints
                ? 'Advanced: lifetime pool only; learned + unspent must stay <= 36.'
                : 'Safe: limited by resulting level and already learned talents.'"
              persistent-hint
              variant="underlined"
            />
          </v-col>
          <v-col cols="4">
            <v-text-field
              v-model="playerData.BaseInventoryCapacity"
              min="0"
              max="2147483647"
              step="1"
              type="number"
              label="Base Inventory Capacity"
              variant="underlined"
            />
          </v-col>
        </v-row>

        <v-row v-if="progressionUnlocked">
          <v-col cols="12">
            <v-switch
              v-model="advancedTalentPoints"
              color="warning"
              density="compact"
              hide-details
              label="Advanced Talent Points — allow future lifetime points early (still capped at 36 total)"
            />
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="3" />
          <v-col cols="3">
            <v-btn
              block
              density="default"
              prepend-icon="mdi-check-circle"
              variant="tonal"
              color="success"
              :disabled="!playerDataChanged"
              @click="savePlayerData()"
            >
              APPLY
            </v-btn>
          </v-col>
          <v-col cols="3">
            <v-btn
              block
              density="default"
              prepend-icon="mdi-refresh"
              variant="tonal"
              color="error"
              :disabled="!playerDataChanged"
              @click="resetPlayerData()"
            >
              RESET
            </v-btn>
          </v-col>
        </v-row>
      </v-container>
    </v-card>
  </div>
</template>

<style lang="scss" scoped>
  .v-card {
    margin-bottom: 20px;
  }
</style>

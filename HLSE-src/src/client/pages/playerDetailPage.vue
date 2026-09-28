<script setup lang="ts">
import { ref, onBeforeMount, computed } from 'vue';
import SaveGameManager from '../managers/saveGame';
import { PlayerData } from '../interfaces';
import { playerChanges, progressionWarning } from '../resources/playerEdits';

const playerData = ref<PlayerData>({} as PlayerData);
const originalData = ref<PlayerData>({} as PlayerData);
const ready = ref(false);
const errorMessage = ref('');
const playerDataChanged = computed(() => ready.value
  && Object.keys(playerChanges(playerData.value, originalData.value)).length > 0);

async function refreshData()
{
  ready.value = false;
  try
  {
    const data = await SaveGameManager.getPlayerData();
    playerData.value = { ...data };
    originalData.value = { ...data };
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
    await SaveGameManager.modifyPlayerData(playerChanges(playerData.value, originalData.value));
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
  <div
    class="d-flex flex-column ma-5"
  >
    <v-card
      density="compact"
    >
      <v-container>
        <v-alert
          type="warning"
          variant="tonal"
          class="mb-4"
        >
          {{ progressionWarning }}
        </v-alert>
        <v-alert
          v-if="errorMessage"
          type="error"
          class="mb-4"
        >
          {{ errorMessage }}
        </v-alert>
        <v-row>
          <v-col
            cols="4"
          >
            <v-text-field
              v-model="playerData.FirstName"
              label="First Name"
              variant="underlined"
            />
          </v-col>
          <v-col
            cols="4"
          >
            <v-text-field
              v-model="playerData.LastName"
              label="Last Name"
              variant="underlined"
            />
          </v-col>
          <v-col
            cols="4"
          >
            <v-combobox
              v-model="playerData.House"
              label="House"
              :items="['Gryffindor', 'Hufflepuff', 'Ravenclaw', 'Slytherin', 'Unaffiliated']"
              variant="underlined"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col
            cols="4"
          >
            <v-text-field
              v-model="playerData.Exp"
              readonly
              type="number"
              label="Experience"
              variant="underlined"
            />
          </v-col>
          <v-col
            cols="4"
          >
            <v-text-field
              v-model="playerData.PerkPoints"
              readonly
              type="number"
              label="Talent Points"
              variant="underlined"
            />
          </v-col>
          <v-col
            cols="4"
          >
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
        <v-row>
          <v-col cols="3" />
          <v-col
            cols="3"
          >
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
          <v-col
            cols="3"
          >
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

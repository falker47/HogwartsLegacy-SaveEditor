<script setup lang="ts">
import { ref, onBeforeMount, watch, reactive, WatchStopHandle } from 'vue';
  import SaveGameManager from '../managers/saveGame';
  import { PlayerData } from '../interfaces';

  const playerData = ref<PlayerData>({} as PlayerData);
  const playerDataChanged = ref(false);

  let changeWatchStop : WatchStopHandle;

  function setupPlayerDataChangeWatch()
  {
    if(changeWatchStop)
    {
      changeWatchStop();
    }
    changeWatchStop = watch(playerData, (newPlayerData : PlayerData) => 
    {
      playerDataChanged.value = true;
    }, { deep: true });
  }

  async function refreshData()
  {
    playerData.value = await SaveGameManager.getPlayerData();
    setupPlayerDataChangeWatch();
  }

  async function resetPlayerData()
  {
    playerDataChanged.value = false;
    await refreshData();
  }

  async function savePlayerData()
  {
    await SaveGameManager.modifyPlayerData(playerData.value);
    await resetPlayerData();
  }

  onBeforeMount(async() =>
  {
    await refreshData();
  });
</script>

<template>
  <div
    class="d-flex flex-column ma-5"
  >
    <v-card
      density="compact"
    >
      <v-container>
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

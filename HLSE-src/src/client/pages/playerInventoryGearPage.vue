<script setup lang="ts">
import { ref, onBeforeMount } from 'vue';

import SaveGameManager from '../managers/saveGame';
import { GearItem } from '../interfaces';

const resourceList = ref<GearItem[]>([]);
const changedResourceList = ref<GearItem[]>([]);

function findExistingChangedItem(searchItem : GearItem) : GearItem | undefined
{
  return changedResourceList.value.find((item) =>
  {
    return item.GearVariation === searchItem.GearVariation;
  });
}

async function updateItem(item : GearItem) : Promise<void>
{
  const existingItem = findExistingChangedItem(item);
  if(existingItem)
  {
    Object.assign(existingItem, item);
  }
  else
  {
    changedResourceList.value.push(item);
  }
}

async function saveData()
{
  for(const changedItem of changedResourceList.value)
  {
    // eslint-disable-next-line no-await-in-loop
    await SaveGameManager.updateGearItem(changedItem);
  }
  changedResourceList.value = [];
}

async function refreshData()
{
  resourceList.value = await SaveGameManager.getPlayerGearInventory();
  changedResourceList.value = [];
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
    <v-container>
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
            :disabled="changedResourceList.length === 0"
            @click="saveData()"
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
            :disabled="changedResourceList.length === 0"
            @click="refreshData()"
          >
            RESET
          </v-btn>
        </v-col>
      </v-row>
    </v-container>
    <v-table
      fixed-header
      height="80vh"
    >
      <thead>
        <tr>
          <th class="text-left">
            Variation
          </th>
          <th class="text-left">
            GearID
          </th>
          <th class="text-left">
            GearLevel
          </th>
          <th class="text-left">
            OffenseStat
          </th>
          <th class="text-left">
            DefenseStat
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in resourceList"
          :key="item.GearVariation"
        >
          <td>{{ item.GearVariation }}</td>
          <td>{{ item.GearID }}</td>
          <td>{{ item.GearLevel }}</td>
          <td>
            <v-text-field
              v-model="item.OffenseStat"
              variant="underlined"
              density="compact"
              type="number"
              hide-details="true"
              @input="updateItem(item)"
            />
          </td>
          <td>
            <v-text-field
              v-model="item.DefenseStat"
              variant="underlined"
              density="compact"
              type="number"
              hide-details="true"
              @input="updateItem(item)"
            />
          </td>
        </tr>
      </tbody>
    </v-table>
  </div>
</template>

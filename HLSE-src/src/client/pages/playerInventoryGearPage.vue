<script setup lang="ts">
import { ref, onBeforeMount, computed } from 'vue';
import SaveGameManager from '../managers/saveGame';
import { GearItem, GearStatEdit } from '../interfaces';

const resourceList = ref<GearItem[]>([]);
const originalList = ref<GearItem[]>([]);
const ready = ref(false);
const saving = ref(false);
const errorMessage = ref('');

function gearIdentity(item : GearItem) : string
{
  return JSON.stringify([ item.SlotNumber, item.GearID, item.GearVariation ]);
}

const changedResourceList = computed<GearStatEdit[]>(() =>
{
  if(!ready.value)
  {
    return [];
  }
  const changes : GearStatEdit[] = [];
  for(const item of resourceList.value)
  {
    const original = originalList.value.find((row) => gearIdentity(row) === gearIdentity(item));
    if(original)
    {
      const patch : GearStatEdit = {
        GearID: original.GearID, GearVariation: original.GearVariation, SlotNumber: original.SlotNumber
      };
      if(String(item.OffenseStat) !== String(original.OffenseStat))
      {
        patch.OffenseStat = item.OffenseStat;
      }
      if(String(item.DefenseStat) !== String(original.DefenseStat))
      {
        patch.DefenseStat = item.DefenseStat;
      }
      if(Object.keys(patch).length > 3)
      {
        changes.push(patch);
      }
    }
  }
  return changes;
});

async function refreshData()
{
  ready.value = false;
  try
  {
    const data = await SaveGameManager.getPlayerGearInventory();
    resourceList.value = data.map((item) => ({ ...item }));
    originalList.value = data.map((item) => ({ ...item }));
    errorMessage.value = '';
    ready.value = true;
  }
  catch (error)
  {
    resourceList.value = [];
    originalList.value = [];
    errorMessage.value = error instanceof Error ? error.message : String(error);
  }
}

async function saveData()
{
  if(!ready.value || saving.value || changedResourceList.value.length === 0)
  {
    return;
  }
  saving.value = true;
  try
  {
    await SaveGameManager.updateGearItems(changedResourceList.value);
    await refreshData();
  }
  catch (error)
  {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  }
  finally
  {
    saving.value = false;
  }
}

onBeforeMount(refreshData);
</script>

<template>
  <div
    class="d-flex flex-column ma-5"
  >
    <v-alert
      type="warning"
      variant="tonal"
      class="mb-4"
    >
      Backpack items only. Edits change the selected item's stored OffenseStat and DefenseStat in DB1.
      The game may recalculate stats; equipped totals and in-game persistence are not yet verified.
      Gear ID, level, traits and other attributes are read-only here.
      Use whole numbers from 0 to 2147483647 (storage bounds, not verified gameplay limits).
      Click Apply, then save/download the modified save file.
    </v-alert>
    <v-alert
      v-if="errorMessage"
      type="error"
      class="mb-4"
    >
      {{ errorMessage }}
    </v-alert>
    <v-alert
      v-if="ready && resourceList.length === 0"
      type="info"
      class="mb-4"
    >
      No backpack gear found in this save.
    </v-alert>
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
            :disabled="!ready || saving || changedResourceList.length === 0"
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
            :disabled="saving || (ready && changedResourceList.length === 0 && !errorMessage)"
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
            Backpack slot
          </th>
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
          :key="gearIdentity(item)"
        >
          <td>{{ item.SlotNumber }}</td>
          <td>{{ item.GearVariation }}</td>
          <td>{{ item.GearID }}</td>
          <td>{{ item.GearLevel }}</td>
          <td>
            <v-text-field
              v-model="item.OffenseStat"
              variant="underlined"
              density="compact"
              type="number"
              min="0"
              max="2147483647"
              step="1"
              :disabled="!ready || saving"
              hide-details="true"
            />
          </td>
          <td>
            <v-text-field
              v-model="item.DefenseStat"
              variant="underlined"
              density="compact"
              type="number"
              min="0"
              max="2147483647"
              step="1"
              :disabled="!ready || saving"
              hide-details="true"
            />
          </td>
        </tr>
      </tbody>
    </v-table>
  </div>
</template>

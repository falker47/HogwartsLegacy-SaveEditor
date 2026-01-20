<script setup lang="ts">
import { ref, onBeforeMount } from 'vue';

import SaveGameManager from '../managers/saveGame';

const perkList = ref<string[]>();

async function refreshData()
{
  perkList.value = await SaveGameManager.getPlayerPerks();
}

async function deletePerk(perkName)
{
  await SaveGameManager.deletePerk(perkName);
  await refreshData();
}

onBeforeMount(async() =>
{
  perkList.value = await SaveGameManager.getPlayerPerks();
});
</script>

<template>
  <div
    class="d-flex flex-column ma-5 bg-surface-variant"
  >
    <v-table
      fixed-header
      height="80vh"
    >
      <thead>
        <tr>
          <th class="text-left">
            Talent
          </th>
          <th class="text-left" />
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="perk in perkList"
          :key="perk"
        >
          <td>{{ perk }}</td>
          <td>
            <v-icon
              size="small"
              class="me-2"
              @click="deletePerk(perk)"
            >
              mdi-delete
            </v-icon>
          </td>
        </tr>
      </tbody>
    </v-table>
  </div>
</template>

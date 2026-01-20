<script setup lang="ts">
  import { ref, onBeforeMount } from 'vue';

  import SaveGameManager from '../managers/saveGame';
  import { PlayerResource } from '../interfaces';

  const resourceList = ref<PlayerResource[]>([]);
  const changedResourceList = ref<PlayerResource[]>([]);

  function findExistingChangedItem(searchItem : PlayerResource) : PlayerResource | undefined
  {
    return changedResourceList.value.find((item) => 
    {
      return item.ItemID === searchItem.ItemID
          && item.HolderID === searchItem.HolderID
          && item.SlotNumber === searchItem.SlotNumber;
    });
  }

  async function updateItem(item : PlayerResource) : Promise<void>
  {
    const existingItem = findExistingChangedItem(item);
    if(existingItem)
    {
      existingItem.Count = item.Count;
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
      await SaveGameManager.modifyPlayerResource(changedItem);
    }
    changedResourceList.value = [];
  }

  async function refreshData()
  {
    resourceList.value = await SaveGameManager.getPlayerResourceInventory();
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
            Holder
          </th>
          <th class="text-left">
            ID
          </th>
          <th class="text-left">
            Name
          </th>
          <th class="text-left">
            Count
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in resourceList"
          :key="item.SlotNumber"
        >
          <td>{{ item.HolderID }}</td>
          <td>{{ item.SlotNumber }}</td>
          <td>{{ item.ItemID }}</td>
          <td>
            <v-text-field
              v-model="item.Count"
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

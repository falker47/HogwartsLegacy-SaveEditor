<script setup lang="ts">
import { ref, onBeforeMount } from 'vue';

import SaveGameManager from '../managers/saveGame';
import { LockState } from '../interfaces';

const lockList = ref<LockState[]>([]);
const updateAllValue = ref(false);
const changedLockList = ref<LockState[]>([]);

function findExistingChangedItem(searchItem : LockState) : LockState | undefined
{
  return changedLockList.value.find((lock) =>
  {
    return lock.LockID === searchItem.LockID;
  });
}

function updateItem(item : LockState) : void
{
  const existingItem = findExistingChangedItem(item);
  if(existingItem)
  {
    existingItem.LockValue = item.LockValue;
  }
  else
  {
    changedLockList.value.push(item);
  }
}

function updateAllItems(lockValue : boolean) : void
{
  for(const lock of lockList.value)
  {
    lock.LockValue = lockValue ? '1' : '0';
    updateItem(lock);
  }
}

async function refreshData()
{
  lockList.value = await SaveGameManager.getGearLocks();
  changedLockList.value = [];
  updateAllValue.value = false;
}

async function saveData()
{
  for(const changedItem of changedLockList.value)
  {
    // eslint-disable-next-line no-await-in-loop
    await SaveGameManager.updateLockState(changedItem);
  }
  await refreshData();
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
            :disabled="changedLockList.length === 0"
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
            :disabled="changedLockList.length === 0"
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
            Gear ID
          </th>
          <th class="text-left">
            <v-switch
              v-model="updateAllValue"
              hide-details
              color="info"
              label="*"
              @click="updateAllItems(updateAllValue)"
            />
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="lock in lockList"
          :key="lock.LockID"
        >
          <td>{{ lock.LockID }}</td>
          <td>
            <v-switch
              v-model="lock.LockValue"
              hide-details
              color="info"
              true-value="0"
              false-value="1"
              @click="updateItem(lock)"
            />
          </td>
        </tr>
      </tbody>
    </v-table>
  </div>
</template>

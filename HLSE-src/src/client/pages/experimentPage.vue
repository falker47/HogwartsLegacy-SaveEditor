<script setup lang="ts">
import { ref, onBeforeMount } from 'vue';
import SaveGameManager from '../managers/saveGame';

const uFastTravel = ref(false);
const uTransItems = ref(false);
const uSpells = ref(false);
const uGear = ref(false);
const uTraits = ref(false);

async function unlockFastTravel()
{
  await SaveGameManager.unlockFastTravelPoints();
  uFastTravel.value = true;
}

async function unlockTransfigurationItems()
{
  await SaveGameManager.unlockTransfigurationItems();
  uTransItems.value = true;
}

async function unlockSpells()
{
  await SaveGameManager.unlockSpells();
  uSpells.value = true;
}

async function unlockGear()
{
  await SaveGameManager.unlockGear();
  uGear.value = true;
}

async function unlockTraits()
{
  await SaveGameManager.unlockTraits();
  uTraits.value = true;
}

</script>

<template>
  <div
    class="d-flex flex-column ma-5 bg-surface-variant"
  >
    <v-alert
      type="warning"
      variant="tonal"
      class="mb-4"
      icon="mdi-lock-open-variant"
    >
      <div class="text-h6">Unlock Abilities</div>
      <div>
        These buttons unlock the <strong>usage</strong> of items (e.g., being able to cast a spell or use a broom). 
        <br>
        To complete your Field Guide (Challenges), use the <strong>Complete Collections</strong> page instead.
      </div>
    </v-alert>

    <v-card>
      <v-card-item>
        <v-card-title>
          <v-icon
            v-if="!uFastTravel"
            size="x-small"
            class="me-2"
            @click="unlockFastTravel()"
          >
            mdi-lock-open-variant
          </v-icon>
          Unlock Fast Travel Locations
        </v-card-title>
      </v-card-item>
    </v-card>
    <v-card>
      <v-card-item>
        <v-card-title>
          <v-icon
            v-if="!uTransItems"
            size="x-small"
            class="me-2"
            @click="unlockTransfigurationItems()"
          >
            mdi-lock-open-variant
          </v-icon>
          Unlock Transfiguration Items
        </v-card-title>
      </v-card-item>
    </v-card>
    <v-card>
      <v-card-item>
        <v-card-title>
          <v-icon
            v-if="!uSpells"
            size="x-small"
            class="me-2"
            @click="unlockSpells()"
          >
            mdi-lock-open-variant
          </v-icon>
          Unlock All Spells
        </v-card-title>
      </v-card-item>
    </v-card>
    <v-card>
      <v-card-item>
        <v-card-title>
          <v-icon
            v-if="!uGear"
            size="x-small"
            class="me-2"
            @click="unlockGear()"
          >
            mdi-lock-open-variant
          </v-icon>
          Unlock All Gear
        </v-card-title>
      </v-card-item>
    </v-card>
    <v-card>
      <v-card-item>
        <v-card-title>
          <v-icon
            v-if="!uTraits"
            size="x-small"
            class="me-2"
            @click="unlockTraits()"
          >
            mdi-lock-open-variant
          </v-icon>
          Unlock All Gear Traits
        </v-card-title>
      </v-card-item>
    </v-card>
  </div>
</template>

<style lang="scss" scoped>
.v-card {
  margin-bottom: 20px;
}

.v-btn {
  margin-right: 5px;
}
</style>

<script setup lang="ts">
import { ref } from 'vue';
import SaveGameManager from '../managers/saveGame';

const uFastTravel = ref(false);
const uTransItems = ref(false);
const uSpells = ref(false);
const uGear = ref(false);
const uTraits = ref(false);

const lFastTravel = ref(false);
const lTransItems = ref(false);
const lSpells = ref(false);
const lGear = ref(false);
const lTraits = ref(false);

async function unlockFastTravel() {
  await SaveGameManager.unlockFastTravelPoints();
  uFastTravel.value = true;
  lFastTravel.value = false;
}
async function lockFastTravel() {
  await SaveGameManager.lockFastTravelPoints();
  lFastTravel.value = true;
  uFastTravel.value = false;
}

async function unlockTransfigurationItems() {
  await SaveGameManager.unlockTransfigurationItems();
  uTransItems.value = true;
  lTransItems.value = false;
}
async function lockTransfigurationItems() {
  await SaveGameManager.lockTransfigurationItems();
  lTransItems.value = true;
  uTransItems.value = false;
}

async function unlockSpells() {
  await SaveGameManager.unlockSpells();
  uSpells.value = true;
  lSpells.value = false;
}
async function lockSpells() {
  await SaveGameManager.lockSpells();
  lSpells.value = true;
  uSpells.value = false;
}

async function unlockGear() {
  await SaveGameManager.unlockGear();
  uGear.value = true;
  lGear.value = false;
}
async function lockGear() {
  await SaveGameManager.lockGear();
  lGear.value = true;
  uGear.value = false;
}

async function unlockTraits() {
  await SaveGameManager.unlockTraits();
  uTraits.value = true;
  lTraits.value = false;
}
async function lockTraits() {
  await SaveGameManager.lockTraits();
  lTraits.value = true;
  uTraits.value = false;
}
</script>

<template>
  <div class="d-flex flex-column ma-5 bg-surface-variant">
    <v-alert
      type="warning"
      variant="tonal"
      class="mb-4"
      icon="mdi-lock-open-variant"
    >
      <div class="text-h6">Unlock / Lock Abilities</div>
      <div>
        <strong>Unlock</strong> buttons enable the <em>usage</em> of items (e.g., casting a spell, using a broom).
        <br>
        <strong>Lock</strong> buttons revert them (useful to fix quest bugs caused by premature unlocks).
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
            color="green"
            @click="unlockFastTravel()"
          >
            mdi-lock-open-variant
          </v-icon>
          <v-icon
            v-if="!lFastTravel"
            size="x-small"
            class="me-2"
            color="red"
            @click="lockFastTravel()"
          >
            mdi-lock
          </v-icon>
          Fast Travel Locations
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
            color="green"
            @click="unlockTransfigurationItems()"
          >
            mdi-lock-open-variant
          </v-icon>
          <v-icon
            v-if="!lTransItems"
            size="x-small"
            class="me-2"
            color="red"
            @click="lockTransfigurationItems()"
          >
            mdi-lock
          </v-icon>
          Transfiguration Items
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
            color="green"
            @click="unlockSpells()"
          >
            mdi-lock-open-variant
          </v-icon>
          <v-icon
            v-if="!lSpells"
            size="x-small"
            class="me-2"
            color="red"
            @click="lockSpells()"
          >
            mdi-lock
          </v-icon>
          All Spells
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
            color="green"
            @click="unlockGear()"
          >
            mdi-lock-open-variant
          </v-icon>
          <v-icon
            v-if="!lGear"
            size="x-small"
            class="me-2"
            color="red"
            @click="lockGear()"
          >
            mdi-lock
          </v-icon>
          All Gear
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
            color="green"
            @click="unlockTraits()"
          >
            mdi-lock-open-variant
          </v-icon>
          <v-icon
            v-if="!lTraits"
            size="x-small"
            class="me-2"
            color="red"
            @click="lockTraits()"
          >
            mdi-lock
          </v-icon>
          All Gear Traits
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

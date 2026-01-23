<script setup lang="ts">
  import { ref } from 'vue';
  import SaveGameManager from '../managers/saveGame';

  const isWorking = ref(false);
  const successMessage = ref('');
  const showSuccess = ref(false);

  async function performUnlock(actionName: string, unlockFn: () => Promise<void>) {
    if (isWorking.value) return;
    
    isWorking.value = true;
    try {
      await unlockFn();
      successMessage.value = `${actionName} Unlocked Successfully!`;
      showSuccess.value = true;
    } catch (e) {
      console.error(e);
      successMessage.value = `Error unlocking ${actionName}`;
      showSuccess.value = true;
    } finally {
      isWorking.value = false;
    }
  }
</script>

<template>
  <div class="d-flex flex-column ma-5">
    <v-card class="mb-5 bg-grey-darken-4">
      <v-card-title class="text-h5">Collection Unlocks</v-card-title>
      <v-card-subtitle>Instantly complete collections for Field Guide challenges.</v-card-subtitle>
      <v-card-text>
        <v-alert type="info" variant="tonal" class="mb-4">
          These actions unlock items in your <strong>Field Guide</strong>. 
          Use "Locks" pages if you want to unlock the <em>ability to use</em> items (like spells or talents).
        </v-alert>
      </v-card-text>
    </v-card>

    <v-row>
      <!-- Conjurations (VERIFIED WORKING) -->
      <v-col cols="12" md="6">
        <v-card height="100%">
          <v-card-title>Room of Requirement</v-card-title>
          <v-card-text>
            Unlock all Furniture, Statues, and Decorations.
            <div class="text-caption text-grey">Complete your Conjurations collection.</div>
          </v-card-text>
          <v-card-actions>
            <v-btn block color="purple" variant="tonal" :loading="isWorking"
              prepend-icon="mdi-magic-staff"
              @click="performUnlock('Conjurations', () => SaveGameManager.unlockAllConjurations())">
              UNLOCK CONJURATIONS
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Coming Soon Placeholder -->
      <v-col cols="12" md="6">
        <v-card height="100%" class="bg-grey-darken-3">
          <v-card-title class="text-grey">More Coming Soon</v-card-title>
          <v-card-text class="text-grey-darken-1">
            Additional unlock features (Field Guide Pages, Cosmetics, Traits) 
            require verified database queries and will be added in future updates.
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-snackbar v-model="showSuccess" color="success" timeout="3000">
      {{ successMessage }}
      <template v-slot:actions>
        <v-btn color="white" variant="text" @click="showSuccess = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

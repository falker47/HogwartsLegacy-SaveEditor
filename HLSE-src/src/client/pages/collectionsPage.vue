<script setup lang="ts">
  import { ref } from 'vue';
  import SaveGameManager from '../managers/saveGame';

  const isWorking = ref(false);
  const successMessage = ref('');
  const showSuccess = ref(false);

  async function unlockConjurations()
  {
    if (isWorking.value) return;
    
    isWorking.value = true;
    try {
      await SaveGameManager.unlockAllConjurations();
      successMessage.value = 'All Conjurations Unlocked!';
      showSuccess.value = true;
    } finally {
      isWorking.value = false;
    }
  }
</script>

<template>
  <div class="d-flex flex-column ma-5">
    <v-card class="mb-5">
      <v-card-title>Collections</v-card-title>
      <v-card-text>
        Unlock all collection items for the Room of Requirement.
        <br>
        <small class="text-grey">Includes all furniture, statues, and decorations.</small>
      </v-card-text>
      
      <v-container>
        <v-row>
          <v-col cols="12" md="6">
            <v-btn
              block
              color="primary"
              variant="tonal"
              prepend-icon="mdi-magic-staff"
              :loading="isWorking"
              @click="unlockConjurations()"
            >
              UNLOCK ALL CONJURATIONS
            </v-btn>
          </v-col>
        </v-row>
      </v-container>
    </v-card>

    <v-snackbar
      v-model="showSuccess"
      color="success"
      timeout="3000"
    >
      {{ successMessage }}
      <template v-slot:actions>
        <v-btn
          color="white"
          variant="text"
          @click="showSuccess = false"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

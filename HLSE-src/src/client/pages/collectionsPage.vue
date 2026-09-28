<script setup lang="ts">
  import { ref } from 'vue';
  import SaveGameManager from '../managers/saveGame';

  const isWorking = ref(false);
  const successMessage = ref('');
  const showSuccess = ref(false);

  const showConfirmDialog = ref(false);
  const pendingAction = ref<(() => Promise<void>) | null>(null);
  const pendingActionName = ref('');

  async function performAction(actionName: string, actionFn: () => Promise<void>) {
    if (isWorking.value) return;
    
    isWorking.value = true;
    try {
      await actionFn();
      successMessage.value = `${actionName} — Done!`;
      showSuccess.value = true;
    } catch (e) {
      console.error(e);
      successMessage.value = `Error: ${actionName}`;
      showSuccess.value = true;
    } finally {
      isWorking.value = false;
    }
  }

  function requestLock(actionName: string, lockFn: () => Promise<void>) {
    pendingActionName.value = actionName;
    pendingAction.value = lockFn;
    showConfirmDialog.value = true;
  }

  async function confirmLock() {
    showConfirmDialog.value = false;
    if (pendingAction.value) {
      await performAction(pendingActionName.value, pendingAction.value);
    }
    pendingAction.value = null;
    pendingActionName.value = '';
  }

  function cancelLock() {
    showConfirmDialog.value = false;
    pendingAction.value = null;
    pendingActionName.value = '';
  }
</script>

<template>
  <div class="d-flex flex-column ma-5">
    <v-card class="mb-5 bg-grey-darken-4">
      <v-card-title class="text-h5">Collection Unlocks / Locks</v-card-title>
      <v-card-subtitle>Collection state editing; challenge completion is not guaranteed.</v-card-subtitle>
      <v-card-text>
        <v-alert type="info" variant="tonal" class="mb-4">
          <strong>Unlock</strong> marks items as obtained in your <strong>Field Guide</strong>.
          <br>
          <strong>Lock</strong> clears collection state, including legitimately collected items. It does not restore a backup.
          <br>
          Use "Locks" pages if you want to toggle the <em>ability to use</em> items (like spells or talents).
        </v-alert>
      </v-card-text>
    </v-card>

    <v-row>
      <!-- Conjurations -->
      <v-col cols="12" md="6">
        <v-card height="100%">
          <v-card-title>Room of Requirement</v-card-title>
          <v-card-text>
            Unlock all Furniture, Statues, and Decorations.
            <div class="text-caption text-grey">Complete your Conjurations collection.</div>
          </v-card-text>
          <v-card-actions class="flex-column ga-2 pa-4">
            <v-btn block color="purple" variant="tonal" :loading="isWorking"
              prepend-icon="mdi-lock-open-variant"
              @click="performAction('Conjurations Unlocked', () => SaveGameManager.unlockAllConjurations())">
              UNLOCK CONJURATIONS
            </v-btn>
            <v-btn block color="error" variant="tonal" :loading="isWorking"
              prepend-icon="mdi-lock"
              @click="requestLock('Conjurations Locked', () => SaveGameManager.lockAllConjurations())">
              LOCK CONJURATIONS
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Appearances -->
      <v-col cols="12" md="6">
        <v-card height="100%">
          <v-card-title>Appearances</v-card-title>
          <v-card-text>
            Unlock all character appearances and outfit variations.
            <div class="text-caption text-grey">Complete your Cosmetics collection.</div>
          </v-card-text>
          <v-card-actions class="flex-column ga-2 pa-4">
            <v-btn block color="pink" variant="tonal" :loading="isWorking"
              prepend-icon="mdi-lock-open-variant"
              @click="performAction('Appearances Unlocked', () => SaveGameManager.unlockAppearances())">
              UNLOCK APPEARANCES
            </v-btn>
            <v-btn block color="error" variant="tonal" :loading="isWorking"
              prepend-icon="mdi-lock"
              @click="requestLock('Appearances Locked', () => SaveGameManager.lockAppearances())">
              LOCK APPEARANCES
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card height="100%">
          <v-card-title>Revelio Pages — unavailable</v-card-title>
          <v-card-text>
            Revelio lore entries and other Field Guide pages use different progress state.
            Page unlock and lock actions are disabled until their effects are verified.
            This editor does not complete page challenges or grant their XP.
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card height="100%">
          <v-card-title>Wand Handles — unavailable</v-card-title>
          <v-card-text>
            Unlock and lock actions are disabled until ownership and usage locks can be
            changed safely. Restoring your backup is the way to undo earlier edits.
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Traits -->
      <v-col cols="12" md="6">
        <v-card height="100%">
          <v-card-title>Traits</v-card-title>
          <v-card-text>
            Unlock all Gear Traits (Level I, II, III).
            <div class="text-caption text-grey">Available to apply at the Loom.</div>
          </v-card-text>
          <v-card-actions class="flex-column ga-2 pa-4">
            <v-btn block color="orange" variant="tonal" :loading="isWorking"
              prepend-icon="mdi-lock-open-variant"
              @click="performAction('Traits Unlocked', () => SaveGameManager.unlockCollectionTraits())">
              UNLOCK TRAITS
            </v-btn>
            <v-btn block color="error" variant="tonal" :loading="isWorking"
              prepend-icon="mdi-lock"
              @click="requestLock('Traits Locked', () => SaveGameManager.lockCollectionTraits())">
              LOCK TRAITS
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Confirmation Dialog -->
    <v-dialog v-model="showConfirmDialog" max-width="450" persistent>
      <v-card>
        <v-card-title class="text-h6">
          <v-icon color="warning" class="me-2">mdi-alert</v-icon>
          Confirm Lock
        </v-card-title>
        <v-card-text>
          This will <strong>revert the entire category</strong> to a locked/not-obtained state,
          including items you may have legitimately collected in-game.
          <br><br>
          This is not a verified quest repair. Restore a backup to undo earlier edits.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="cancelLock()">Cancel</v-btn>
          <v-btn color="error" variant="tonal" @click="confirmLock()">Lock</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Success Snackbar -->
    <v-snackbar v-model="showSuccess" color="success" timeout="3000">
      {{ successMessage }}
      <template v-slot:actions>
        <v-btn color="white" variant="text" @click="showSuccess = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

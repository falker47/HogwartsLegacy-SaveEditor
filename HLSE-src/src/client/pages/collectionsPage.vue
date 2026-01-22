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

  function downloadURL(data: string, fileName: string)
  {
    const hiddenDownloadLink = document.createElement('a');
    hiddenDownloadLink.href = data;
    hiddenDownloadLink.download = fileName;
    document.body.appendChild(hiddenDownloadLink);
    hiddenDownloadLink.style.display = 'none';
    hiddenDownloadLink.click();
    hiddenDownloadLink.remove();
  }

  function downloadBlob(data: Uint8Array, fileName: string, mimeType: string)
  {
    const blob = new Blob([ data as any ], {
      type: mimeType
    });

    const url = URL.createObjectURL(blob);

    downloadURL(url, fileName);

    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  async function downloadSave()
  {
    isWorking.value = true;
    try {
      const saveFile = await SaveGameManager.generateSaveFile();
      downloadBlob(saveFile, 'hlsave.sav', 'application/octet-stream');
      successMessage.value = 'Save File Generated & Downloaded!';
      showSuccess.value = true;
    } catch(e) {
      console.error(e);
      successMessage.value = 'Error generating save file.';
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
      <v-card-subtitle>Instantly complete collections for 100% completion challenges.</v-card-subtitle>
      <v-card-text>
        <v-alert type="info" variant="tonal" class="mb-4">
          These actions unlock items in your <strong>Field Guide</strong>. 
          Use "Locks" pages if you want to unlock the <em>ability to use</em> items (like spells or talents).
        </v-alert>
      </v-card-text>
    </v-card>

    <v-row>
      <!-- Field Guide -->
      <v-col cols="12" md="6">
        <v-card height="100%">
          <v-card-title>Field Guide Pages</v-card-title>
          <v-card-text>
            Unlock all "Revelio Pages" lore entries.
            <div class="text-caption text-grey">Great for leveling up and challenges.</div>
          </v-card-text>
          <v-card-actions>
            <v-btn block color="primary" variant="tonal" :loading="isWorking"
              prepend-icon="mdi-book-open-page-variant"
              @click="performUnlock('Field Guide Pages', () => SaveGameManager.unlockRevelioPages())">
              UNLOCK PAGES
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Conjurations -->
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

      <!-- Cosmetics -->
      <v-col cols="12" md="6">
        <v-card height="100%">
          <v-card-title>Cosmetics</v-card-title>
          <v-card-text>
            Unlock all Appearances and Wand Handles.
            <div class="text-caption text-grey">Access all transmogs and wand skins.</div>
          </v-card-text>
          <v-card-actions>
            <v-btn block color="pink" variant="tonal" :loading="isWorking"
              prepend-icon="mdi-tshirt-crew"
              @click="performUnlock('Cosmetics', () => SaveGameManager.unlockCosmetics())">
              UNLOCK COSMETICS
            </v-btn>
          </v-card-actions>
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
          <v-card-actions>
            <v-btn block color="orange" variant="tonal" :loading="isWorking"
              prepend-icon="mdi-shield-star"
              @click="performUnlock('Traits', () => SaveGameManager.unlockTraits())">
              UNLOCK TRAITS
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-divider class="my-4" />

    <v-card class="bg-surface-variant">
      <v-card-item>
        <v-card-title>Save Changes</v-card-title>
        <v-card-subtitle>Done unlocking? Download your modified save file.</v-card-subtitle>
      </v-card-item>
      <v-card-text>
        <v-btn
          block
          color="success"
          size="large"
          prepend-icon="mdi-content-save-download"
          @click="downloadSave"
        >
          GENERATE & DOWNLOAD SAVE
        </v-btn>
      </v-card-text>
    </v-card>

    <v-snackbar v-model="showSuccess" color="success" timeout="3000">
      {{ successMessage }}
      <template v-slot:actions>
        <v-btn color="white" variant="text" @click="showSuccess = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
  import { ref } from 'vue';
  import { useRouter } from 'vue-router';
  const router = useRouter();

  import AppManager from '../managers/application';
  import SaveGameManager from '../managers/saveGame';

  import { downloadBlob } from '../lib/blobUtils';

  const appState = AppManager.appState;
  const uploadError = ref('');
  const loading = ref(false);

  async function downloadSave()
  {
    const saveFile = await SaveGameManager.generateSaveFile();
    downloadBlob(saveFile, 'hlsave.sav', 'application/octet-stream');
  }

  async function uploadFileClick()
  {
    document.getElementById('fileUploadElement').click();
  }

  async function handleFileUpload(event)
  {
    const ele = event.target || event.srcElement;
    const file = ele?.files?.[0];
    if(!file || loading.value) return;
    loading.value = true;
    uploadError.value = '';
    try
    {
      const fileBuffer = await file.arrayBuffer();
      await AppManager.loadSaveGameData(fileBuffer);
      await router.push('/playerDetail');
    }
    catch (error)
    {
      uploadError.value = error instanceof Error ? error.message : String(error);
    }
    finally
    {
      loading.value = false;
      ele.value = '';
    }
  }
</script>
<template>
  <v-list>
    <v-alert v-if="uploadError" type="error" class="ma-2">
      Could not open save: {{ uploadError }}
    </v-alert>
    <v-list-item>
      <v-btn
        block
        class="mb-4"
        density="default"
        prepend-icon="mdi-upload"
        variant="tonal"
        color="info"
        :disabled="loading"
        @click="uploadFileClick()"
      >
        UPLOAD SAVE
      </v-btn>
      <v-btn
        block
        :disabled="loading || !appState.isSaveFileLoaded"
        density="default"
        prepend-icon="mdi-download"
        color="success"
        variant="tonal"
        @click="downloadSave()"
      >
        DOWNLOAD SAVE
      </v-btn>
      <input
        id="fileUploadElement"
        type="file"
        hidden
        @change="handleFileUpload"
      >
    </v-list-item>
  </v-list>
</template>

<script setup lang="ts">
  import { useRouter } from 'vue-router';
  const router = useRouter();

  import AppManager from '../managers/application';
  import SaveGameManager from '../managers/saveGame';

  import { downloadBlob } from '../lib/blobUtils';

  const appState = AppManager.appState;

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
    const ele = event.srcElement;
    const files = Array.from(ele.files);
    console.log(files);
    const fileBuffer = await files[0].arrayBuffer();
    await AppManager.loadSaveGameData(fileBuffer);
    await router.push('/playerDetail');
  }
</script>
<template>
  <v-list>
    <v-list-item>
      <v-btn
        block
        class="mb-4"
        density="default"
        prepend-icon="mdi-upload"
        variant="tonal"
        color="info"
        @click="uploadFileClick()"
      >
        UPLOAD SAVE
      </v-btn>
      <v-btn
        block
        :disabled="!appState.isSaveFileLoaded"
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

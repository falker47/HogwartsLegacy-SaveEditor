<script setup lang="ts">
  import { ref, onBeforeMount } from 'vue';
  import SaveGameManager from '../managers/saveGame';
  import AppManager from '../managers/application';

  let dbUpload1 : Uint8Array | null = null;
  let dbUpload2 : Uint8Array | null = null;

  function downloadURL(data, fileName)
  {
    const hiddenDownloadLink = document.createElement('a');
    hiddenDownloadLink.href = data;
    hiddenDownloadLink.download = fileName;
    document.body.appendChild(hiddenDownloadLink);
    hiddenDownloadLink.style.display = 'none';
    hiddenDownloadLink.click();
    hiddenDownloadLink.remove();
  }

  function downloadBlob(data, fileName, mimeType)
  {
    const blob = new Blob([ data ], {
      type: mimeType
    });

    const url = URL.createObjectURL(blob);

    downloadURL(url, fileName);

    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  async function downloadSave()
  {
    const saveFile = await SaveGameManager.generateSaveFile();
    downloadBlob(saveFile, 'hlsave.sav', 'application/octet-stream');
  }

  async function downloadCustomSave()
  {
    const saveFile = await SaveGameManager.generateSaveFile(dbUpload1, dbUpload2);
    downloadBlob(saveFile, 'hlcustomsave.sav', 'application/octet-stream');
  }

  async function downloadDB(secondary : boolean)
  {
    const dbFile = await SaveGameManager.getDatabase(secondary);
    downloadBlob(dbFile, secondary ? 'sqldb2.sqlite' : 'sqldb1.sqlite', 'application/octet-stream');
  }

  async function handleDB1FileUpload(event)
  {
    const ele = event.srcElement;
    const files = Array.from(ele.files);
    const fileBuffer = await files[0].arrayBuffer();
    dbUpload1 = new Uint8Array(fileBuffer);
  }

  async function handleDB2FileUpload(event)
  {
    const ele = event.srcElement;
    const files = Array.from(ele.files);
    const fileBuffer = await files[0].arrayBuffer();
    dbUpload2 = new Uint8Array(fileBuffer);
  }

</script>

<template>
  <div class="d-flex flex-column ma-5 bg-surface-variant">
    <v-card>
      <v-card-item>
        <v-card-title>Save Game</v-card-title>
        <v-card-subtitle>Download a save game with the current DB modifications in it.</v-card-subtitle>
      </v-card-item>
      <v-card-text>
        <v-btn
          color="secondary"
          @click="downloadSave"
        >
          Download
        </v-btn>
      </v-card-text>
    </v-card>
    <v-card>
      <v-card-item>
        <v-card-title>Databases</v-card-title>
        <v-card-subtitle>Download the databases in this save file for external modification.</v-card-subtitle>
      </v-card-item>
      <v-card-text>
        <v-btn
          color="secondary"
          @click="downloadDB(false)"
        >
          Download Database 1
        </v-btn>
        <v-btn
          color="secondary"
          @click="downloadDB(true)"
        >
          Download Database 2
        </v-btn>
      </v-card-text>
    </v-card>
    <v-card>
      <v-card-item>
        <v-card-title>Custom DB Upload</v-card-title>
        <v-card-subtitle>
          Create a save file using uploaded databases (only changes in the uploaded DBs will be applied).
        </v-card-subtitle>
      </v-card-item>
      <v-card-text>
        <v-file-input
          label="Database 1"
          density="compact"
          @change="handleDB1FileUpload"
        />
        <v-file-input
          label="Database 2"
          density="compact"
          @change="handleDB2FileUpload"
        />
        <v-btn
          color="secondary"
          @click="downloadCustomSave"
        >
          Generate Save File
        </v-btn>
      </v-card-text>
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

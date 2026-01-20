<script setup lang="ts">
  import AppManager from './managers/application';

  import FileHandlerComponent from './components/fileHandler.vue';
  import NavigationListComponent from './components/navigationList.vue';
</script>
<template>
  <v-layout>
    <v-app-bar title="Hogwarts Legacy Save Game Editor" />
    <v-navigation-drawer permanent>
      <FileHandlerComponent />
      <v-divider />
      <NavigationListComponent v-if="AppManager.appState.isSaveFileLoaded" />
    </v-navigation-drawer>
    <v-main style="min-height: 300px;">
      <router-view />
    </v-main>
  </v-layout>
</template>
<style lang="scss">
  html { overflow-y: auto }
</style>

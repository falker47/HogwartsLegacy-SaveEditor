<script setup lang="ts">
  import { ref } from 'vue';
  import { useRouter } from 'vue-router';
  import FastTravelLocksPage from '../pages/fastTravelLocksPage.vue';
  import GearLocksPage from '../pages/gearLocksPage.vue';
  import TraitsLocksPage from '../pages/traitsLocksPage.vue';
  import TransfigurationLocksPage from '../pages/transfigurationLocksPage.vue';
  const router = useRouter();

  const currentTitle = ref('Player Data');

  async function onItemClick(navItem)
  {
    currentTitle.value = navItem.title;
    await router.push(navItem.path);
  }

  const navList = [
    {
      title: 'Player Data',
      icon: 'mdi-account',
      path: '/playerDetail'
    },
    {
      title: 'Resources',
      icon: 'mdi-format-list-bulleted',
      path: '/playerResources'
    },
    {
      title: 'Combat Resources',
      icon: 'mdi-bottle-soda',
      path: '/playerCombatResources'
    },
    {
      title: 'Mission Resources',
      icon: 'mdi-exclamation-thick',
      path: '/playerMissionResources'
    },
    {
      title: 'Gear List',
      icon: 'mdi-hanger',
      path: '/playerInventoryGear'
    },
    {
      title: 'Talents',
      icon: 'mdi-magic-staff',
      path: '/playerPerks'
    },
    {
      title: 'Spell Locks',
      icon: 'mdi-lock',
      path: '/spellLocks'
    },
    {
      title: 'Fast Travel Locks',
      path: '/fastTravelLocks',
      icon: 'mdi-lock'
    },
    {
      title: 'Gear Locks',
      path: '/gearLocks',
      icon: 'mdi-lock'
    },
    {
      title: 'Trait Locks',
      path: '/traitLocks',
      icon: 'mdi-lock'
    },
    {
      title: 'Transfiguration Locks',
      path: '/transfigurationLocks',
      icon: 'mdi-lock'
    },
    {
      title: 'Unlocks',
      icon: 'mdi-lock-open-variant',
      path: '/experiments'
    },
    {
      title: 'Save File',
      icon: 'mdi-content-save-move',
      path: '/saveFile'
    }
  ];

</script>
<template>
  <v-list>
    <v-list-item
      v-for="item in navList"
      :key="item.title"
      :active="item.title === currentTitle"
      :title="item.title"
      :prepend-icon="item.icon"
      active-color="secondary"
      @click="onItemClick(item)"
    />
  </v-list>
</template>

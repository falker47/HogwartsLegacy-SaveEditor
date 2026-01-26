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
    { type: 'header', title: 'Player' },
    {
      title: 'Player Data',
      icon: 'mdi-account',
      path: '/playerDetail'
    },
    {
      title: 'Save File',
      icon: 'mdi-content-save-move',
      path: '/saveFile'
    },

    { type: 'header', title: 'Resources & Inventory' },
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

    { type: 'divider' },
    { type: 'header', title: 'Lock Managers' },
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

    { type: 'divider' },
    { type: 'header', title: 'Bulk Tools' },
    {
      title: 'Unlock Abilities',
      icon: 'mdi-lock-open-check',
      path: '/experiments'
    },
    {
      title: 'Complete Collections',
      path: '/collections',
      icon: 'mdi-book-check'
    }
  ];

</script>
<template>
  <v-list>
    <template v-for="(item, index) in navList" :key="index">
      <v-list-subheader v-if="item.type === 'header'" class="text-high-emphasis font-weight-bold">
        {{ item.title }}
      </v-list-subheader>
      
      <v-divider v-else-if="item.type === 'divider'" class="my-2" />
      
      <v-list-item
        v-else
        :active="item.title === currentTitle"
        :title="item.title"
        :prepend-icon="item.icon"
        active-color="secondary"
        @click="onItemClick(item)"
      />
    </template>
  </v-list>
</template>

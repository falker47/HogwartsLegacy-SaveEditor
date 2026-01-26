import { createApp } from 'vue';
import { createRouter, createMemoryHistory } from 'vue-router';

import 'vuetify/styles';
import '@mdi/font/css/materialdesignicons.css';

import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';

import App from './app.vue';

// Pages
import DefaultPage from './pages/defaultPage.vue';
import PlayerResourcesPage from './pages/playerResourcesPage.vue';
import PlayerCombatsResourcesPage from './pages/playerCombatResourcesPage.vue';
import PlayerMissionResourcesPage from './pages/playerMissionResourcesPage.vue';
import PlayerPerksPage from './pages/playerPerksPage.vue';
import PlayerDetailPage from './pages/playerDetailPage.vue';
import SaveFilePage from './pages/saveFilePage.vue';
import ExperimentsPage from './pages/experimentPage.vue';
import PlayerInventoryGearPage from './pages/playerInventoryGearPage.vue';

import SpellLocksPage from './pages/spellLocksPage.vue';
import FastTravelLocksPage from './pages/fastTravelLocksPage.vue';
import GearLocksPage from './pages/gearLocksPage.vue';
import TraitsLocksPage from './pages/traitsLocksPage.vue';
import TransfigurationLocksPage from './pages/transfigurationLocksPage.vue';
import CollectionsPage from './pages/collectionsPage.vue';

const vuetify = createVuetify({
    components,
    directives,
    theme: {
        defaultTheme: 'dark'
    }
});

const routes = [
    { path: '/', component: DefaultPage },
    { path: '/playerDetail', component: PlayerDetailPage },
    { path: '/playerResources', component: PlayerResourcesPage },
    { path: '/playerCombatResources', component: PlayerCombatsResourcesPage },
    { path: '/playerMissionResources', component: PlayerMissionResourcesPage },
    { path: '/playerInventoryGear', component: PlayerInventoryGearPage },
    { path: '/playerPerks', component: PlayerPerksPage },
    { path: '/spellLocks', component: SpellLocksPage },
    { path: '/fastTravelLocks', component: FastTravelLocksPage },
    { path: '/gearLocks', component: GearLocksPage },
    { path: '/traitLocks', component: TraitsLocksPage },
    { path: '/transfigurationLocks', component: TransfigurationLocksPage },
    { path: '/collections', component: CollectionsPage },
    { path: '/experiments', component: ExperimentsPage },
    { path: '/saveFile', component: SaveFilePage }
];

const router = createRouter({
    history: createMemoryHistory(),
    routes
});

const theApp = createApp(App);

theApp.use(router);
theApp.use(vuetify);
theApp.mount('#app');

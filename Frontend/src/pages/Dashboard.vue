<script setup lang="ts">
import { ref, watch } from 'vue';
import DefaultLayout from '@/layouts/DefaultLayout.vue';
import MapSimulation from '@/components/MapSimulation.vue';
import RouteForm from '@/components/RouteForm.vue';
import WeatherWidget from '../components/WeatherWidget.vue';
import Loader from '@/components/Loader.vue';

export interface Route {
  route: [number, number][];
  distance_km: number;
  is_optimal: boolean;
}

const routes = ref<Route[]>([]);  // Инициализируем пустым массивом, а не undefined
const selectedRouteIndex = ref(0);
const isLoading = ref(false);

function updateRoutes(newRoutes: Route[]) {
  routes.value = newRoutes;
  isLoading.value = false;
}

function updateSelectedRouteIndex(newIndex: number) {
  selectedRouteIndex.value = newIndex;
}

function startLoading() {
  isLoading.value = true;
}

function endLoading() {
  isLoading.value = false;
}

watch(
  routes,
  (newVal) => {
    console.log('Routes changed:', newVal);
  },
  { immediate: true }
);
</script>

<template>
  <DefaultLayout>
    <div class="relative w-full h-full">
      <!-- Карта -->
      <MapSimulation 
        class="z-0" 
        :routes="routes" 
        :selectedRouteIndex="selectedRouteIndex"
        @update:selectedRouteIndex="updateSelectedRouteIndex"
      />
      <RouteForm 
        :routes="routes"
        :selectedRouteIndex="selectedRouteIndex"
        :isLoading="isLoading"
        @updateRoutes="updateRoutes"
        @updateSelectedRouteIndex="updateSelectedRouteIndex"
        @startLoading="startLoading"
        @endLoading="endLoading"
      />
      <div class="weather-widget-wrapper">
        <WeatherWidget />
      </div>
      <Loader v-if="isLoading" />
    </div>  
  </DefaultLayout>
</template>

<style scoped>
.relative {
  width: 100%;
  height: 100%;
  position: relative;
}

.z-0 {
  z-index: 0;
}

.weather-widget-wrapper {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000; /* Чтобы перекрывать остальные элементы */
}
</style>

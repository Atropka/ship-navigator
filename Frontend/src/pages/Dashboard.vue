<script setup lang="ts">
import { ref, watch } from 'vue';
import DefaultLayout from '@/layouts/DefaultLayout.vue';
import MapSimulation from '@/components/MapSimulation.vue';
import RouteForm from '@/components/RouteForm.vue';

const routes = ref<[number, number][]>([]); // Массив маршрута, который будет обновляться
watch(
      () => routes,
      (newCoords) => {
        console.log(newCoords)
       
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
        :routeCoordinates="routes" 
      />
      <RouteForm 
        v-model:modelValue="routes"  
      />
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
</style>

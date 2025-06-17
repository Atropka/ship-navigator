<script setup lang="ts">
import "leaflet/dist/leaflet.css";
import { LMap, LTileLayer, LMarker, LPolyline } from "@vue-leaflet/vue-leaflet";
import { ref, computed, watch } from "vue";
import L from "leaflet";
import type { Route } from '../pages/Dashboard.vue';

interface Port {
  id: number;
  name: string;
  lat: number;
  lon: number;
}

const props = defineProps<{
  routes: Route[];
  selectedRouteIndex: number;
}>();

const zoom = ref(10);
const center = ref<[number, number]>([59.94, 30.23]);
const ports = ref<Port[]>([]);
const waterPaths = ref<[number, number][][]>([]);
const leafletMap = ref<L.Map | null>(null);
const routes = computed(() => props.routes || []);
const otherRoutes = computed(() =>
  routes.value.filter((r, idx) => idx !== props.selectedRouteIndex && r?.route?.length > 1)
);

const portIcon = L.icon({
  iconUrl: 'https://cdn-icons-png.flaticon.com/512/684/684908.png', // иконка корабля
  iconSize: [32, 32], // размер иконки
  iconAnchor: [16, 32], // точка привязки к координате
  popupAnchor: [0, -32], // позиция попапа относительно иконки
});

const loadPorts = async () => {
  try {
    const res = await fetch("http://localhost:8000/api/api/ports/");
    const data = await res.json();
    ports.value = data.map((port: any) => ({
      id: port.id,
      name: port.name,
      lat: port.latitude,
      lon: port.longitude,
    }));
  } catch (error) {
    console.error("Error loading ports:", error);
  }
};

const onMapReady = (mapInstance: L.Map) => {
  leafletMap.value = mapInstance;
  loadPorts();
  // fetchWaterGraph()
};

const currentRoute = computed(() => {
  if (
    props.routes &&
    props.routes.length > 0 &&
    props.selectedRouteIndex >= 0 &&
    props.selectedRouteIndex < props.routes.length
  ) {
    return props.routes[props.selectedRouteIndex];
  }
  return { route: [] } as unknown as Route;
});

watch(
  currentRoute,
  (route) => {
    if (!leafletMap.value) return;

    if (!route || !Array.isArray(route.route) || route.route.length < 2) {
      leafletMap.value.setView(center.value, zoom.value);
      return;
    }

    const bounds = L.latLngBounds(
      route.route.map(([lat, lon]) => L.latLng(lat, lon))
    );
    leafletMap.value.fitBounds(bounds, { padding: [50, 50] });
  },
  { immediate: true }
);
</script>

<template>
  <l-map
    :zoom="zoom"
    :center="center"
    style="height: 100vh; width: 100vw; display: block;"
    @ready="onMapReady"
  >
    <l-tile-layer
      url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
      subdomains="abcd"
      :max-zoom="20"
    />

    <!-- Все маршруты кроме выбранного серым цветом -->
    <l-polyline
  v-for="(route, idx) in otherRoutes"
  :key="`alt-route-${idx}`"
  :lat-lngs="route.route"
  color="#999999"
  weight="3"
  opacity="0.3"
/>

    <!-- Выбранный маршрут зеленым -->
    <l-polyline
  v-if="currentRoute && currentRoute.route.length > 1"
  :lat-lngs="currentRoute.route"
  color="limegreen"
  weight="7"
  opacity="0.3"
  class="glow-blur"
/>
<l-polyline
  v-if="currentRoute && currentRoute.route.length > 1"
  :lat-lngs="currentRoute.route"
  color="limegreen"
  weight="2"
  opacity="0.9"
/>

    <!-- Морские пути -->
    <l-polyline
      v-for="(path, index) in waterPaths"
      :key="`water-path-${index}`"
      :lat-lngs="path"
      color="green"
      weight="3"
      opacity="0.5"
    />

    <!-- Порты -->
    <l-marker
      v-for="port in ports"
      :icon="portIcon"
      :key="port.id"
      :lat-lng="[port.lat, port.lon]"
    >
      <template #popup>
        {{ port.name }}
      </template>
    </l-marker>
  </l-map>
</template>

<style scoped>
/* Можно убрать, т.к. стиль инлайн, но если хотите использовать id, добавить в l-map */
#map {
  height: 100vh;
  width: 100vw;
}

.glow-blur {
  filter: url(#blur-filter);;
}
</style>

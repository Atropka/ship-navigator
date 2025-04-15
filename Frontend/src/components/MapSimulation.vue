<template>
  <l-map
    :zoom="zoom"
    :center="center"
    style="height: 100vh; width: 100vw; display: block;"
    @ready="onMapReady"
  >
    <l-tile-layer
      :url="'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'"
      :attribution="'&copy; <a href=\'https://www.openstreetmap.org/copyright\'>OpenStreetMap</a> contributors &copy; <a href=\'https://carto.com/attributions\'>CARTO</a>'"
      :subdomains="'abcd'"
      :max-zoom="20"
    />

    <!-- Отображение маршрута -->
    <l-polyline
      v-if="routeCoordinates?.length > 1"
      :lat-lngs="routeCoordinates"
      color="blue"
      weight="5"
      opacity="0.7"
    />

    <!-- Отображение морских путей -->
    <l-polyline
      v-for="(path, index) in waterPaths"
      :key="index"
      :lat-lngs="path"
      color="green"
      weight="3"
      opacity="0.5"
    />

    <!-- Отображение портов -->
    <l-marker
      v-for="(port, index) in ports"
      :key="index"
      :lat-lng="[port.lat, port.lon]"
    >
      <template #popup>
        {{ port.name }}
      </template>
    </l-marker>
  </l-map>
</template>

<script lang="ts">
import "leaflet/dist/leaflet.css";
import { LMap, LTileLayer, LMarker, LPolyline } from "@vue-leaflet/vue-leaflet";
import { defineComponent, ref, watch } from "vue";
import L from "leaflet";

export default defineComponent({
  components: {
    LMap,
    LTileLayer,
    LMarker,
    LPolyline,
  },
  props: {
    routeCoordinates: {
      type: Array as () => [number, number][],
      required: true,
    },
  },
  setup(props) {
    const zoom = ref(10);
    const center = ref([59.94, 30.23]);
    const ports = ref([]); // Список портов
    const waterPaths = ref([]); // Список водных путей
    const leafletMap = ref<L.Map | null>(null);

    // Функция для загрузки портов
    const loadPorts = async () => {
      const res = await fetch("http://localhost:8000/api/api/ports/");
      const data = await res.json();
      ports.value = data.map((port: any) => ({
        name: port.name,
        lat: port.latitude,
        lon: port.longitude,
      }));
    };

    // Функция для загрузки водных путей из Overpass API
    const loadWaterPaths = async (lat: number, lon: number, radius: number = 20000) => {
      const overpassUrl = "http://overpass-api.de/api/interpreter";
      const overpassQuery = `
        [out:json];
        way["waterway"](around:${radius},${lat},${lon});
        out body;
        >;
        out skel qt;
      `;
      const response = await fetch(overpassUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `data=${overpassQuery}`,
      });

      const data = await response.json();

      // Обработка данных, преобразуем в список координат
      const paths = [];
      data.elements.forEach((element: any) => {
        if (element.nodes) {
          const path = [];
          element.nodes.forEach((nodeId: any) => {
            const node = data.elements.find((el: any) => el.id === nodeId);
            if (node) {
              path.push([node.lat, node.lon]);
            }
          });
          if (path.length > 0) {
            paths.push(path);
          }
        }
      });

      waterPaths.value = paths;
    };

    // Сохраняем Leaflet карту при ready
    const onMapReady = (mapInstance: L.Map) => {
      leafletMap.value = mapInstance;
      loadPorts(); // Загружаем порты при инициализации карты
      loadWaterPaths(center.value[0], center.value[1]); // Загружаем водные пути для начальной точки карты
    };

    watch(
      () => props.routeCoordinates,
      (newCoords) => {
        if (!leafletMap.value || newCoords.length < 2) return;

        const bounds = L.latLngBounds(
          newCoords.map((coord) => L.latLng(coord[0], coord[1]))
        );
        leafletMap.value.fitBounds(bounds);
      },
      { immediate: true }
    );

    return {
      zoom,
      center,
      ports,
      waterPaths,
      onMapReady,
    };
  },
});
</script>

<style scoped>
#map {
  width: 100%;
  height: 100%;
}
</style>

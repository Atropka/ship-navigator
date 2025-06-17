<script setup lang="ts">
import { ref, onMounted, defineEmits, defineProps, computed, watch } from 'vue';
import type { Route } from '../pages/Dashboard.vue';

const props = defineProps<{
  routes: Route[];
  selectedRouteIndex: number;
  isLoading: boolean
}>();

const emit = defineEmits<{
  (e: 'updateRoutes', value: Route[]): void;
  (e: 'updateSelectedRouteIndex', value: number): void;
  (e: 'startLoading'): void;
  (e: 'endLoading'): void;
}>();

const startPortId = ref<number | null>(null);
const endPortId = ref<number | null>(null);
const ports = ref<{ id: number; name: string; lat: number; lon: number }[]>([]);

const startPort = computed(() => ports.value.find(p => p.id === startPortId.value) ?? null);
const endPort = computed(() => ports.value.find(p => p.id === endPortId.value) ?? null);

const loadPorts = async () => {
  try {
    emit('startLoading');
    const res = await fetch('http://localhost:8000/api/api/ports/');
    if (!res.ok) throw new Error(`Ошибка загрузки портов: ${res.status}`);
    const data = await res.json();
    ports.value = data.map((port: any) => ({
      id: port.id,
      name: port.name,
      lat: port.latitude,
      lon: port.longitude,
    }));
  } catch (e) {
    alert('Не удалось загрузить порты');
    console.error(e);
  } finally {
    emit('endLoading');
  }
};

const calculateRoute = async () => {
  emit('startLoading'); 
  if (!startPort.value || !endPort.value) {
    alert('Пожалуйста, выберите начальный и конечный порты');
    return;
  }
  try {
    const response = await fetch('http://localhost:8000/api/calculate_route/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        start_port_id: startPort.value.id,
        end_port_id: endPort.value.id,
      }),
    });
    const result = await response.json();
    if (response.ok && Array.isArray(result.routes)) {
      emit('updateRoutes', result.routes);
      emit('updateSelectedRouteIndex', 0);
      localSelectedRouteIndex.value = 0;
    } else {
      alert('Ошибка при получении маршрутов с сервера');
      console.error(result);
    }
  } catch (error) {
    alert('Ошибка при запросе маршрутов');
    console.error(error);
  }
  finally {
    emit('endLoading');
  }
};

const localSelectedRouteIndex = ref(props.selectedRouteIndex);

watch(() => props.selectedRouteIndex, (newIndex) => {
  localSelectedRouteIndex.value = newIndex;
});

const selectRoute = (idx: number) => {
  localSelectedRouteIndex.value = idx;
  emit('updateSelectedRouteIndex', idx);
};

onMounted(() => {
  loadPorts();
});
</script>

<template>
  <div class="route-panel">
    <div class="header">
      <h3>Построить маршрут</h3>
    </div>

    <div class="form-group">
      <label class="select-label" for="startPort">
        <div
          class="circle-indicator"
          :class="{ active: startPortId !== null }"
        ></div>
        Откуда
      </label>
      <select v-model="startPortId" id="startPort" class="custom-select">
        <option :value="null" disabled>Выберите порт</option>
        <option v-for="port in ports" :key="port.id" :value="port.id">
          {{ port.name }}
        </option>
      </select>
    </div>

    <div class="form-group">
      <label class="select-label" for="endPort">
        <div
          class="circle-indicator"
          :class="{ active: endPortId !== null }"
        ></div>
        Куда
      </label>
      <select v-model="endPortId" id="endPort" class="custom-select">
        <option :value="null" disabled>Выберите порт</option>
        <option v-for="port in ports" :key="port.id" :value="port.id">
          {{ port.name }}
        </option>
      </select>
    </div>

    <div class="actions">
      <button @click="calculateRoute" class="btn-calculate">Рассчитать</button>
    </div>

    <div class="form-group" v-if="props.routes.length > 0" style="margin-top: 15px;">
      <label for="routeSelect">Выберите маршрут</label>
      <div
    class="route-carousel"
    v-if="props.routes.length > 0"
  >
    <div
      v-for="(route, idx) in props.routes"
      :key="idx"
      class="route-button"
      :class="{ active: localSelectedRouteIndex === idx }"
      @click="selectRoute(idx)"
      :title="`Маршрут ${idx + 1} — ${route.distance_km.toFixed(2)} км`"
    >
      <div class="route-number">Маршрут {{ idx + 1 }}</div>
      <div class="route-distance">{{ route.distance_km.toFixed(2) }} км</div>
      <div v-if="route.is_optimal" class="optimal-label">оптимальный</div>
    </div>
  </div>
    </div>
  </div>
</template>

<style scoped>

.route-carousel {
  margin-top: 15px;
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 8px;
  scrollbar-width: thin;
  scrollbar-color: #4caf50 transparent;
}

/* Стили для скролла (для WebKit) */
.route-carousel::-webkit-scrollbar {
  height: 6px;
}
.route-carousel::-webkit-scrollbar-track {
  background: transparent;
}
.route-carousel::-webkit-scrollbar-thumb {
  background-color: #4caf50;
  border-radius: 3px;
}

/* Кнопки маршрутов */
.route-button {
  flex: 0 0 auto;
  background-color: #f0f0f0;
  border-radius: 10px;
  padding: 10px 14px;
  cursor: pointer;
  min-width: 110px;
  box-shadow: 0 0 5px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  user-select: none;
  transition: background-color 0.3s, box-shadow 0.3s;
  font-size: 14px;
  color: #555;
}

.route-button:hover {
  background-color: #d9f0d9;
  box-shadow: 0 0 10px rgba(76,175,80,0.4);
}

/* Активная кнопка */
.route-button.active {
  background-color: #4caf50;
  color: white;
  box-shadow: 0 0 12px rgba(76,175,80,0.7);
  font-weight: 700;
}

/* Подписи внутри кнопки */
.route-number {
  font-weight: 600;
  margin-bottom: 4px;
}

.route-distance {
  font-size: 13px;
  margin-bottom: 4px;
}

.optimal-label {
  font-size: 11px;
  background: #2e7d32;
  padding: 2px 6px;
  border-radius: 12px;
  color: #c8e6c9;
  user-select: none;
}

.route-panel {
  position: absolute;
  top: 80px;
  left: 10px;
  background: white;
  padding: 20px 24px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  width: 320px; /* расширена ширина */
}

.select-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 6px;
  color: #333;
}

/* Круглый индикатор слева от селекта */
.circle-indicator {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background-color: #bbb;
  transition: background-color 0.3s;
  flex-shrink: 0;
}
.circle-indicator.active {
  background-color: #4caf50;
}

/* Селекты без бордеров и с кастомным стилем */
.custom-select {
  width: 100%;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  background-color: #f9f9f9;
  font-size: 14px;
  outline-offset: 2px;
  transition: box-shadow 0.3s, background-color 0.3s;
  cursor: pointer;
}

/* При фокусе - зеленая подсветка */
.custom-select:focus {
  background-color: #e6f4ea;
  box-shadow: 0 0 6px 2px rgba(76, 175, 80, 0.6);
  outline: none;
}

/* Также при выборе селекта (не null) добавим немного фона */
.custom-select:not([value="null"]):not(:invalid) {
  background-color: #e6f4ea;
}

/* Кнопка рассчитать */
.btn-calculate {
  background-color: #4caf50;
  color: white;
  padding: 10px 14px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.3s;
}

.btn-calculate:hover {
  background-color: #43a047;
}

.form-group {
  margin-bottom: 14px;
  display: flex;
  flex-direction: column;
}

.actions {
  display: flex;
  justify-content: flex-end;
}
</style>

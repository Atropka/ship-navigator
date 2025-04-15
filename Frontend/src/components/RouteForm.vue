<script setup lang="ts">
import { ref, onMounted, defineEmits, defineProps } from 'vue';

const props = defineProps<{
  modelValue: [number, number][]; // Получаем координаты маршрута от родителя
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: [number, number][]): void; // Отправляем обновленные координаты маршрута
}>();

const showModal = ref(false);
const startPort = ref<any | null>(null);
const endPort = ref<any | null>(null);
const ports = ref<any[]>([]);

// Загружаем порты при монтировании
const loadPorts = async () => {
  const res = await fetch('http://localhost:8000/api/api/ports/');
  const data = await res.json();
  ports.value = data.map((port: any) => ({
    id: port.id,
    name: port.name,
    lat: port.latitude,
    lon: port.longitude,
  }));
};

// Вычисление маршрута
const calculateRoute = async () => {
  if (startPort.value && endPort.value) {
    const response = await fetch('http://localhost:8000/api/calculate_route/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        start_port_id: startPort.value.id,
        end_port_id: endPort.value.id,
      }),
    });

    const result = await response.json();
    if (response.ok && Array.isArray(result.route_coords)) {
      emit('update:modelValue', result.route_coords); // Обновляем координаты маршрута
      showModal.value = false;
    } else {
      console.error('Некорректный ответ сервера:', result);
    }
  } else {
    alert('Пожалуйста, выберите начальный и конечный порты');
  }
};

// Загружаем порты при монтировании компонента
onMounted(() => {
  loadPorts();
});
</script>

<template>
  <!-- Кнопка для открытия модального окна -->
  <button @click="showModal = true" class="btn-open-modal">Open Route Calculator</button>

  <!-- Модальное окно -->
  <div v-if="showModal" class="modal-overlay">
    <div class="modal">
      <div class="modal-header">
        <h3>Calculate Route</h3>
      </div>
      <div class="modal-body">
        <!-- Селект для выбора начальной точки -->
        <div>
          <label for="startPort">Select Start Port:</label>
          <select v-model="startPort" id="startPort">
            <option v-for="port in ports" :key="port.id" :value="port">{{ port.name }}</option>
          </select>
        </div>

        <!-- Селект для выбора конечной точки -->
        <div>
          <label for="endPort">Select End Port:</label>
          <select v-model="endPort" id="endPort">
            <option v-for="port in ports" :key="port.id" :value="port">{{ port.name }}</option>
          </select>
        </div>
      </div>
      <div class="modal-footer">
        <button @click="showModal = false" class="btn-cancel">Cancel</button>
        <button @click="calculateRoute" class="btn-calculate">Calculate</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Стили для модального окна и кнопок */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}
.modal {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  width: 400px;
}
.modal-header {
  font-size: 18px;
  font-weight: bold;
}
.modal-footer {
  display: flex;
  justify-content: space-between;
}
.btn-open-modal {
  background-color: #007bff;
  color: white;
  padding: 10px;
  border: none;
  cursor: pointer;
}
.btn-cancel {
  background-color: #f44336;
  color: white;
  padding: 10px;
  border: none;
  cursor: pointer;
}
.btn-calculate {
  background-color: #4caf50;
  color: white;
  padding: 10px;
  border: none;
  cursor: pointer;
}
</style>

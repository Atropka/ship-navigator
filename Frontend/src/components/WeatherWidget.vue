<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';

const latitude = 59.94;
const longitude = 30.31;

const temperature = ref<number | null>(null);
const windspeed = ref<number | null>(null);
const weatherCode = ref<number | null>(null);
const error = ref<string | null>(null);

// Простое сопоставление weatherCode Open-Meteo в иконки и текст
// https://open-meteo.com/en/docs#latitude=52.52&longitude=13.41&current_weather=true
const weatherIcon = computed(() => {
  if (weatherCode.value === null) return '';
  const code = weatherCode.value;

  if ([0].includes(code)) return '☀️';           // Clear sky
  if ([1, 2, 3].includes(code)) return '☁️';    // Mainly clear, partly cloudy, overcast
  if ([45, 48].includes(code)) return '🌫️';    // Fog, depositing rime fog
  if ([51, 53, 55, 56, 57].includes(code)) return '🌦️'; // Drizzle
  if ([61, 63, 65, 66, 67].includes(code)) return '🌧️'; // Rain
  if ([71, 73, 75, 77].includes(code)) return '❄️';    // Snow
  if ([80, 81, 82].includes(code)) return '🌧️';  // Rain showers
  if ([85, 86].includes(code)) return '❄️';     // Snow showers
  if ([95, 96, 99].includes(code)) return '⛈️'; // Thunderstorm
  return '❓'; // Unknown
});

const fetchWeather = async () => {
  try {
    const res = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current_weather=true`
    );
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    const data = await res.json();
    temperature.value = data.current_weather.temperature;
    windspeed.value = data.current_weather.windspeed;
    weatherCode.value = data.current_weather.weathercode;
  } catch (e: any) {
    error.value = e.message || 'Ошибка при загрузке погоды';
  }
};

onMounted(() => {
  fetchWeather();
});
</script>

<template>
  <div class="weather-widget">
    <div v-if="error" class="error">{{ error }}</div>
    <div v-else-if="temperature !== null" class="weather-info">
      <div class="weather-details">
        <p>Температура:     {{ temperature }}°C</p>
        <p>Ветер:      {{ windspeed }} км/ч</p>
      </div>
      <span class="weather-icon">{{ weatherIcon }}</span>
    </div>
    <div v-else>Загрузка погоды...</div>
  </div>
</template>

<style scoped>
.weather-widget {
  background: rgba(255, 255, 255, 0.85);
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  color: #222;
  width: 200px;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 12px;
}
.weather-info{
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.weather-icon {
  font-size: 36px;
  line-height: 1;
  user-select: none;
}

.weather-details p {
  margin: 0;
}

.error {
  color: red;
  font-weight: bold;
}
</style>

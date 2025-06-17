<template>
    <div class="loader-overlay">
      <p>Loading<span>{{ dots }}</span></p>
      <div class="spinner"></div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, onMounted, onUnmounted } from 'vue';
  
  const dots = ref('');
  let intervalId: number;
  
  onMounted(() => {
    intervalId = window.setInterval(() => {
      dots.value = dots.value.length < 3 ? dots.value + '.' : '';
    }, 500);
  });
  
  onUnmounted(() => {
    clearInterval(intervalId);
  });
  </script>
  
  <style scoped>
  .loader-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-color: rgba(255, 255, 255, 0.75);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 2000;
  }
  
  .spinner {
    border: 6px solid #f3f3f3;
    border-top: 6px solid #4caf50;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    animation: spin 1s linear infinite;
    margin-top: 10px;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg);}
    100% { transform: rotate(360deg);}
  }
  </style>
  
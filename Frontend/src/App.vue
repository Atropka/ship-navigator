<template>
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700&display=swap" rel="stylesheet">

  <router-view />

  <svg style="position: absolute; width: 0; height: 0;" aria-hidden="true" focusable="false" >
  <defs>
    <filter id="blur-filter" x="-20%" y="-20%" width="140%" height="140%" >
      <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="limegreen" flood-opacity="0.6" />
    </filter>
  </defs>
</svg>
</template>


<script setup lang="ts">
</script>

<style>
body {
  font-family: 'Manrope', sans-serif;
}
</style>

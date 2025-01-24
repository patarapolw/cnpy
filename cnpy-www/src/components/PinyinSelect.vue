<template>
  <div style="font-family: sans-serif">
    <div id="pinyin-select"></div>
    <button type="button" id="warnings">Warning list...</button>
    <div><small id="warning-items"></small></div>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
#pinyin-select {
  margin-bottom: 1em;
}

.checkbox {
  width: 3em;
  display: inline-flex;
  flex-direction: row;
}

.checkbox > input[type="checkbox"]:not(:checked) + input[type="checkbox"] {
  display: none;
}

[data-pinyin-count="1"] .checkbox > input[type="checkbox"] + input[type="checkbox"] {
  display: none;
}
</style>

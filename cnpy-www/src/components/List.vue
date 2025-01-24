<template>
  <ol
    id="editor"
    contenteditable
    autocomplete="off"
    autocorrect="off"
    autocapitalize="none"
    spellcheck="false"
  ></ol>
</template>

<script setup lang="ts"></script>

<style lang="scss" scoped>
body {
  margin-bottom: 50px;
}

ol {
  /* font-family: monospace; */
  white-space: pre;

  &:focus {
    outline: none;
  }
}

li::marker {
  font-size: 10px;
  font-family: Arial, Helvetica, sans-serif;
  color: grey;
}
</style>

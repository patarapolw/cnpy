<template>
  <main>
    <form>
      <input
        type="text"
        name="type"
        id="type"
        autocomplete="off"
        autocorrect="off"
        autocapitalize="off"
        spellcheck="false"
        lang="zh-CN"
      />
      <input type="submit" hidden />
    </form>
    <div style="overflow: auto">
      <ol></ol>
    </div>
  </main>
</template>

<script setup lang="ts"></script>

<style scoped>
* {
  font-family: sans-serif;
}

main {
  display: grid;
  grid-template-rows: auto 1fr;
  height: 100vh;
  box-sizing: border-box;
  margin: 0;
}

form {
  display: flex;
  flex-direction: row;
}

input {
  flex-grow: 1;
}

.pinyin {
  font-size: 0.7em;
  display: inline-block;
  color: gray;
  margin-left: 1em;
  user-select: none;
  cursor: default;
}

.pinyin:not(:hover) {
  opacity: 0.2;
}

.pinyin::before {
  content: "\09";
}

li::marker {
  font-size: 10px;
  font-family: Arial, Helvetica, sans-serif;
  color: grey;
}
</style>

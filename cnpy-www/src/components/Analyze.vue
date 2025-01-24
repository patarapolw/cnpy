<template>
  <fieldset id="analyzer" class="active">
    <textarea
      autocomplete="off"
      autocorrect="off"
      autocapitalize="off"
      spellcheck="false"
    />
    <footer>
      <button type="submit">Analyze</button>
    </footer>
  </fieldset>
  <fieldset id="result">
    <div style="overflow: auto">
      <ol />
    </div>
    <footer>
      <button type="reset">Edit</button>
    </footer>
  </fieldset>
</template>

<script setup lang="ts"></script>

<style lang="scss" scoped>
* {
  font-family: sans-serif;
}

fieldset {
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  margin: 0;
  display: none;
  border: none;
  grid-template-rows: 1fr auto;

  &.active {
    display: grid;
  }

  footer {
    margin-top: 5px;
    display: flex;
    flex-direction: row-reverse;
  }
}

.pinyin {
  font-size: 0.7em;
  display: inline-block;
  color: gray;
  margin-left: 1em;
  user-select: none;
  cursor: default;

  &:not(:hover) {
    opacity: 0.2;
  }

  &::before {
    content: "\09";
  }
}

li::marker {
  font-size: 10px;
  font-family: Arial, Helvetica, sans-serif;
  color: grey;
}
</style>

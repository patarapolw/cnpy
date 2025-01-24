<template>
  <table>
    <thead>
      <tr>
        <th scope="col">Lv</th>
        <th scope="col" />
      </tr>
    </thead>
    <tbody>
      <tr v-for="(r, i) in rows" :key="i">
        <th scope="row" class="checkbox">
          <input type="checkbox" data-level="" />
          <span class="level" />
        </th>

        <td>
          <div class="voc-container" />
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup lang="ts">
import { ref } from "vue";

const rows = ref([]);
</script>

<style lang="scss" scoped>
table {
  max-width: 1000px;
  margin: 1em auto;
  border-collapse: collapse;
}

thead {
  visibility: collapse;
}

tr:has(:checked) {
  background-color: aliceblue;
}

th,
td {
  border: 1px solid gray;
}

.voc-container {
  display: flex;
  flex-wrap: wrap;
  margin-bottom: 0.5em;
}

.voc {
  display: inline-flex;
  cursor: default;

  &:not(:last-child)::after {
    content: "，";
  }

  &:hover {
    font-size: 1.5em;
    padding: 0 10px;
    margin-left: -10px;
    margin-right: -0.5rem;
    box-shadow: inset 0px 0px 0.5em 0.5em rgba(255, 255, 255, 0.5);
    border-radius: 0.3em;
    z-index: 1;
  }

  &:hover::after {
    content: "";
  }
}
</style>

<template>
  <div class="top-nav">
    <span class="button">
      <a href="./quiz.html">
        Start Quiz
        <span id="due-count" />
      </a>
    </span>
  </div>

  <div class="dashboard">
    <small class="nav">
      <div style="flex-grow: 1" />
      <div class="nav-content">
        <a href="./list.html?f=vocab/vocab.txt" target="new_window">Add vocab</a>
      </div>
      <div class="nav-content">
        <a href="./levels.html" target="new_window">Levels</a>
      </div>
      <div class="nav-content">
        <a href="./analyze.html" target="new_window">Text</a>
      </div>
      <div class="nav-content">
        <a href="./list.html?f=skip/skip.txt" target="new_window">Skip</a>
      </div>
    </small>

    <div class="count-dashboard">
      <span id="learned-count" />
    </div>

    <div id="hanzi-list" lang="zh-CN" />
  </div>
</template>

<script setup lang="ts"></script>

<style lang="scss" scoped>
* {
  font-family: sans-serif;
}

/* Hide the scrollbar for Chrome, Safari and Opera */
::-webkit-scrollbar {
  display: none;
}

/* Hide the scrollbar for Internet Explorer, Edge and Firefox */
* {
  -ms-overflow-style: none; /* Internet Explorer and Edge */
  scrollbar-width: none; /* Firefox */
}

body {
  margin: 25px;
}

.top-nav {
  text-align: center;
  margin-bottom: 1em;
}

#due-count small {
  font-size: 0.7em;
}

.nav {
  display: flex;
  flex-direction: row;
  align-items: center;

  > .nav-content {
    display: block;
  }

  > .nav-content + .nav-content::before {
    content: "・";
  }
}

.count-dashboard {
  text-align: center;
  margin-bottom: 1em;
}

#hanzi-list {
  display: flex;
  flex-wrap: wrap;
}

.hanzi {
  display: inline-flex;
  cursor: default;
  z-index: 0;

  &:hover,
  &.hover {
    font-size: 2em;
    padding: 0 3px;
    margin: 0 -0.7rem;
    box-shadow: inset 0px 0px 0.5em 0.5em rgba(255, 255, 255, 0.9);
    z-index: 1;
  }
}

.tier-0 {
  color: black;
}

.tier-1 {
  color: peru;
}

.tier-2 {
  color: skyblue;
}

.tier-3 {
  color: #eee;

  &.hover,
  &:hover {
    color: #ccc;
  }
}

.button {
  border: 1px solid rgba(0, 0, 0, 0.8);
  border-radius: 3px;
  padding: 5px 10px;
  background-color: rgba(211, 211, 211, 0.5);

  a {
    text-decoration: none;
  }
}
</style>

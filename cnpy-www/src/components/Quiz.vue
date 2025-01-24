<template>
  <div id="quiz">
    <nav class="top-nav hide-showcase" id="progress">
      <div data-count-type="right"></div>
      <div data-count-type="repeat"></div>
      <div data-count-type="wrong"></div>
    </nav>
    <nav id="counter" class="nav hide-showcase">
      <div class="left"></div>

      <div class="center nav">
        <span class="count" data-count-type="right">0</span>
        <span>:</span>
        <span class="count" data-count-type="repeat" data-repeat="">0</span>
        <span data-repeat="">:</span>
        <span class="count" data-count-type="wrong">0</span>

        <span>/</span>

        <span class="count" data-count-type="total" data-repeat="">20</span>

        <span>&nbsp;(</span>
        <span class="count" data-count-type="due">-</span>
        <span>)</span>
      </div>

      <div class="right">
        <div>
          <a class="internal-link" href="./dashboard.html">&#x1F519;</a>
        </div>
      </div>
    </nav>

    <div id="vocab" lang="zh-CN">&nbsp;</div>

    <div id="status"></div>

    <div
      contenteditable
      id="type-input"
      class="hide-showcase"
      autocomplete="off"
      autocorrect="off"
      autocapitalize="off"
      spellcheck="false"
      data-checked=""
    ></div>
    <a
      id="type-compare"
      class="internal-link"
      target="new_window"
      title="Specify valid Pinyin"
    ></a>
    <div id="check-buttons-area" class="buttons if-checked hide-showcase" data-checked="">
      <button
        class="if-wrong"
        data-checked=""
        style="background-color: lightcoral"
        onclick="mark('wrong')"
      >
        Wrong
      </button>
      <button
        class="if-wrong if-right if-wrong:not-repeat"
        data-checked=""
        data-repeat=""
        style="background-color: gold"
        onclick="mark('repeat')"
      >
        Not Sure
      </button>
      <button
        class="if-right"
        data-checked=""
        style="background-color: greenyellow"
        onclick="mark('right')"
      >
        Right
      </button>
    </div>

    <details id="dictionary-entries" class="if-checked" data-checked="">
      <summary>Dictionary</summary>
      <div class="external-links">
        <a
          href="https://en.wiktionary.org/wiki/__voc__#Chinese"
          target="_blank"
          rel="noopener noreferrer"
          >Wiktionary</a
        >
        /
        <a
          href="https://www.mdbg.net/chinese/dictionary?page=worddict&wdrst=0&wdqb=__voc__&email="
          target="_blank"
          rel="noopener noreferrer"
          >MDBG</a
        >
        /
        <a
          href="https://www.zdic.net/hans/__voc__"
          target="_blank"
          rel="noopener noreferrer"
          >zdic</a
        >
        /
        <a
          href="https://youglish.com/pronounce/__voc__/chinese"
          target="_blank"
          rel="noopener noreferrer"
          >YouGlish</a
        >
        /
        <a
          href="https://duckduckgo.com/?t=ffab&q=__voc__+词典&ia=web"
          target="_blank"
          rel="noopener noreferrer"
          >DuckDuckGo</a
        >
      </div>

      <template>
        <blockquote class="if-checked-details">
          <header>
            <span class="simp" lang="zh-CN"></span>
            <span class="trad" lang="zh-TW"></span>

            <span class="pinyin"></span>
          </header>
          <ul class="english"></ul>
        </blockquote>
      </template>
    </details>

    <details id="sentences" class="if-checked" data-checked="" data-sentence-count="">
      <summary>Sentences</summary>
      <template>
        <li class="if-checked-details">
          <span class="simp" lang="zh-CN"></span>
          <ul>
            <li class="english"></li>
          </ul>
        </li>
      </template>
    </details>

    <details id="notes" class="if-checked" data-checked="" data-has-notes="" open>
      <summary>Notes</summary>
      <fieldset id="notes-edit">
        <textarea
          class="notes-display"
          autocomplete="off"
          autocorrect="off"
          autocapitalize="off"
          spellcheck="false"
        ></textarea>
        <footer>
          <button type="submit">Save</button>
        </footer>
      </fieldset>
      <fieldset id="notes-show">
        <div style="overflow: scroll">
          <div class="notes-display" lang="zh-CN"></div>
        </div>
        <footer>
          <button type="button">Edit</button>
        </footer>
      </fieldset>
    </details>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
#quiz {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

/* Hide the scrollbar for Chrome, Safari and Opera */
:not(textarea)::-webkit-scrollbar {
  display: none;
}

/* Hide the scrollbar for Internet Explorer, Edge and Firefox */
:not(textarea) {
  -ms-overflow-style: none; /* Internet Explorer and Edge */
  scrollbar-width: none; /* Firefox */
}

#quiz > * {
  margin-bottom: 10px;
}

#quiz:not([data-type="standard"]) #counter,
#quiz:not([data-type="standard"]) #check-buttons-area,
#quiz[data-type="show"] .hide-showcase {
  display: none;
}

details,
p,
.nav,
.count,
[contenteditable] {
  font-family: Arial, Helvetica, sans-serif;
}

.nav {
  display: flex;
  flex-flow: row wrap;
  align-items: center;
  width: 95%;
}

a.internal-link {
  text-decoration: none;
}

a.internal-link:visited {
  color: inherit;
}

.nav > .left {
  text-align: left;
  width: 33%;
}

.nav > .center {
  text-align: center;
  justify-content: center;
  width: 34%;
}

.nav > .right {
  text-align: right;
  width: 33%;
}

.top-nav {
  display: flex;
  flex-direction: row;
  width: 100vw;
  box-sizing: border-box;
}

.top-nav#progress [data-count-type] {
  height: 2px;
}

.top-nav#progress [data-count-type="right"] {
  background-color: forestgreen;
}

.top-nav#progress [data-count-type="repeat"] {
  background-color: orange;
}

.top-nav#progress [data-count-type="wrong"] {
  background-color: red;
}

#counter {
  cursor: default;
}

.count[data-count-type="total"][data-repeat="true"] {
  text-decoration: underline;
  color: red;
}

.count small {
  font-size: 0.7em;
}

#vocab {
  font-size: 80px;
  cursor: default;
}

#type-input {
  text-align: center;
  border: 2px solid black;
  border-radius: 3px;
  padding: 2px 1.5em;
  min-width: calc(200px - 3em);
}

#type-input[data-checked="right"] {
  caret-color: transparent;
  background-color: greenyellow;
}

#type-input[data-checked="wrong"] {
  caret-color: transparent;
  background-color: lightcoral;
}

#type-input[data-checked="warn"] {
  animation: shake 0.82s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
  transform: translate3d(0, 0, 0);
  backface-visibility: hidden;
  perspective: 1000px;
}

@keyframes shake {
  10%,
  90% {
    transform: translate3d(-1px, 0, 0);
  }

  20%,
  80% {
    transform: translate3d(2px, 0, 0);
  }

  30%,
  50%,
  70% {
    transform: translate3d(-4px, 0, 0);
  }

  40%,
  60% {
    transform: translate3d(4px, 0, 0);
  }
}

#type-compare[data-pinyin-count="1"] {
  color: initial;
}

#type-compare b {
  font-family: sans-serif;
}

.if-checked[data-checked=""] {
  display: none;
}

.if-right,
.if-wrong {
  display: none;
}

.if-right[data-checked="right"] {
  display: inline-block;
}

.if-wrong[data-checked="wrong"] {
  display: inline-block;
}

.if-wrong\:not-repeat[data-repeat="true"][data-checked="wrong"] {
  display: none;
}

.buttons > button:not(:first) {
  margin-left: 1em;
}

details {
  width: 80vw;
  text-align: left;
}

summary {
  cursor: pointer;
}

.external-links {
  margin-top: 0.5em;
  text-align: center;
}

.dictionary-entry header :not(:first-child) {
  margin-left: 1em;
}

.english {
  font-size: 10px;
}

#sentences .english:not(:hover) {
  color: lightgray;
}

#sentences[data-sentence-count="0"] {
  display: none;
}

#notes fieldset {
  display: none;
  height: 150px;
  width: 100%;
  margin-top: 5px;
  grid-template-rows: 1fr auto;
}

#notes[data-has-notes=""] fieldset {
  border: none;
}

#notes[data-has-notes=""] fieldset#notes-edit {
  display: grid;
}

#notes:not([data-has-notes=""]) fieldset#notes-show {
  display: grid;
}

#notes fieldset .notes-display {
  flex-grow: 1;
  min-width: none;
}

#notes fieldset footer {
  margin-top: 5px;
  display: flex;
  flex-direction: row-reverse;
}
</style>

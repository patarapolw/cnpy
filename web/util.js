//@ts-check

import { api } from "./api.js";

const utterance = new SpeechSynthesisUtterance();
utterance.lang = "zh-CN";

/**
 *
 * @param {string} s
 */
export function speak(s) {
  let elAudio = Array.from(document.querySelectorAll("audio")).find((el) =>
    el.hasAttribute("data-tts")
  );
  if (!elAudio) {
    elAudio = document.createElement("audio");
    elAudio.setAttribute("data-tts", "true");
    elAudio.style.display = "none";
  }

  elAudio.onerror = () => {
    utterance.text = s;
    speechSynthesis.speak(utterance);
  };

  elAudio.src = `/api/tts/${s}.mp3`;
  elAudio.currentTime = 0;
  elAudio.play();
}

/**
 *
 * @param {string} s
 * @param {boolean} [isFuzzy]
 * @returns
 */
export function normalize_pinyin(s, isFuzzy) {
  s = s
    .replace(/[vü]/g, "u:")
    .replace(/[^a-z1-5:]/gi, "")
    .toLocaleLowerCase()
    .replace(/(\d)er5/g, "$1r5");
  if (isFuzzy) {
    s = s.replace(/\d+/g, " ");
  }
  return s;
}

/**
 *
 * @param {string} a
 * @param {string} b
 * @param {boolean} [isFuzzy]
 * @returns
 */
export function comp_pinyin(a, b, isFuzzy) {
  return normalize_pinyin(a, isFuzzy) === normalize_pinyin(b, isFuzzy);
}

/**
 *
 * @param {string} v
 */
export async function openItem(v) {
  const r = await api.set_vocab_for_quiz(v);
  if (r.ok) {
    api.new_window("./quiz.html", v);
  } else {
    alert(`Invalid vocab: ${v}`);
  }
}

/**
 *
 * @param {string} v
 * @param {string[]} ps
 */
export async function searchPinyin(v, ps) {
  const u = new URL(location.href);
  u.pathname = "/search.html";

  ps = ps
    .map((p) => p.toLocaleLowerCase().replace(/\d/g, ""))
    .filter((a, i, r) => r.indexOf(a) === i);
  u.searchParams.set("q", ps.length > 1 ? `(${ps.join("|")})` : ps[0]);

  api.new_window(u.pathname + u.search, "Similar pinyin to " + v);
}

/**
 *
 * @param {string} voc
 */
export async function searchVoc(voc) {
  const u = new URL(location.href);
  u.pathname = "/search.html";
  u.searchParams.set("q", JSON.stringify({ voc }));
  api.new_window(u.pathname + u.search, "Word containing " + voc);
}

/**
 *
 * @param {string} rad
 */
export async function searchRad(rad) {
  const u = new URL(location.href);
  u.pathname = "/search.html";
  u.searchParams.set("q", JSON.stringify({ rad }));
  api.new_window(u.pathname + u.search, "Hanzi containing " + rad);
}

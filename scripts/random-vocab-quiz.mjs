//@ts-check

import { readFile } from "fs/promises";
import readline from "readline/promises";

import sqlite3 from "better-sqlite3";
import { paste } from "copy-paste";

// AI web may block browser automation, e.g. puppeteer
import puppeteer from "puppeteer-core";

const db = sqlite3("user/llm.db");

const vocList = await readFile("user/vocab/vocab.txt", "utf-8").then((s) =>
  s
    .trim()
    .split("\n")
    .map((v) => v.trim())
);
const randomVoc = () => vocList[Math.floor(Math.random() * vocList.length)];

/**
 *
 * @param {string} v
 * @returns
 */
const prompt = (v) =>
  `Is the following a correct meaning for ${v} in Chinese?`.trim();

const browser = await puppeteer.connect({
  browserURL: `http://localhost:9222`,
  defaultViewport: null, // Use the default viewport size
});

try {
  let APP = "gemini";
  let APP_URL = "https://gemini.google.com/app";
  let SEL_TEXTAREA = ".ql-editor";

  switch (APP) {
    case "chatgpt":
      APP_URL = "https://chatgpt.com";
      SEL_TEXTAREA = "#prompt-textarea";
      break;
    case "gemini":
      APP_URL = "https://gemini.google.com/app";
      SEL_TEXTAREA = ".ql-editor";
      break;
  }

  db.exec(/* sql */ `
  CREATE TABLE IF NOT EXISTS "${APP}" (
    v     TEXT NOT NULL PRIMARY KEY,
    [url] TEXT NOT NULL
  );
`);

  const page = await browser.newPage();

  const stmt = db.prepare(`SELECT [url] FROM "${APP}" WHERE v = :v`);
  const insertStmt = db.prepare(
    `INSERT INTO "${APP}" (v, [url]) VALUES (:v, :url) ON CONFLICT DO NOTHING`
  );

  let v = "";
  let url = APP_URL;

  page.on("framenavigated", () => {
    if (!v) return;

    url = page.url();
    if (url === APP_URL) return;

    insertStmt.run({ v, url });
  });

  /**
   *
   * @param {string} s
   */
  async function openVocab(s) {
    if (!/^\p{sc=Han}+$/u.test(s)) return;

    v = s;
    console.log(v);

    url =
      /** @type {{ url: string } | null} */ (stmt.get({ v }))?.url || APP_URL;

    if (url !== page.url()) {
      await page.goto(url);
    }

    if (url === APP_URL) {
      await page.waitForSelector(SEL_TEXTAREA);
      await page.keyboard.type(prompt(v));
    }
  }

  async function loopInput() {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    });

    while (true) {
      v = v || randomVoc();
      openVocab(v);

      v = await rl.question("Next word: ");
    }
  }

  async function watchClipboard() {
    while (true) {
      const s = await new Promise((resolve, reject) => {
        paste((err, text) => {
          err ? reject(err) : resolve(text);
        });
      });

      if (s && /^\p{sc=Han}+$/u.test(s) && s !== v) {
        openVocab(v);
      }

      await new Promise((resolve) => setTimeout(resolve, 5000));
    }
  }

  await Promise.all([loopInput()]);
} finally {
  await browser.disconnect();
  db.close();
}

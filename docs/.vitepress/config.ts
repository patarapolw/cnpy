import { defineConfig } from "vitepress";

const hskLevels = [
  { hsk: 1, from: 1, to: 5 },
  { hsk: 2, from: 6, to: 10 },
  { hsk: 3, from: 11, to: 20 },
  { hsk: 4, from: 21, to: 30 },
  { hsk: 5, from: 31, to: 40 },
  { hsk: 6, from: 41, to: 60 },
];

export default defineConfig({
  base: "/cnpy/",
  title: "cnpy",
  description:
    "Chinese vocabulary levels with pinyin and dictionary definitions.",
  themeConfig: {
    nav: [
      { text: "Home", link: "/" },
      { text: "App guide", link: "/guide" },
      { text: "Vocabulary", link: "/levels/" },
    ],
    sidebar: [
      {
        text: "Using cnpy",
        items: [
          { text: "App guide", link: "/guide" },
          { text: "Reading quiz", link: "/guide#reading-quiz" },
          { text: "Meanings and notes", link: "/guide#meanings-and-notes" },
          { text: "Hanzi and text tools", link: "/guide#hanzi-and-text-tools" },
          { text: "Statistics and settings", link: "/guide#statistics-and-settings" },
          { text: "Data sources", link: "/guide#data-sources" },
        ],
      },
      {
        text: "Vocabulary levels",
        link: "/levels/",
        items: hskLevels.map(({ hsk, from, to }) => ({
          text: `HSK ${hsk}`,
          link: `/levels/hsk-${hsk}/`,
          collapsed: true,
          items: Array.from({ length: to - from + 1 }, (_, index) => {
            const level = from + index;
            return {
              text: `Level ${level}`,
              link: `/levels/hsk-${hsk}/level-${level}`,
            };
          }),
        })),
      },
    ],
    socialLinks: [
      { icon: "github", link: "https://github.com/patarapolw/cnpy" },
    ],
  },
});

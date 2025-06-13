import adapter from "@sveltejs/adapter-netlify";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),

  kit: {
    adapter: adapter(),
    alias: {
      "$py/*": "src/python/*",
    },
    output: {
      preloadStrategy: "preload-mjs",
    },
  },
};

export default config;

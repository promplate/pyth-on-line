import adapter from "@sveltejs/adapter-auto";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

const vercelOrigin = process.env.VERCEL && `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`;
const netlifyOrigin = process.env.NETLIFY && process.env.DEPLOY_PRIME_URL;

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),

  kit: {
    adapter: adapter(),
    prerender: {
      origin: process.env.SITE_URL ?? vercelOrigin ?? netlifyOrigin,
    },
    alias: {
      "$py/*": "src/python/*",
    },
    output: {
      preloadStrategy: "preload-mjs",
    },
  },
};

export default config;

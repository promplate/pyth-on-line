import { sveltekitOG } from "@ethercorps/sveltekit-og/plugin";
import adapter from "@sveltejs/adapter-auto";
import vercel from "@sveltejs/adapter-vercel";
import { sveltekit } from "@sveltejs/kit/vite";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";
import dir2json from "rollup-plugin-flatten-dir";
import Unocss from "unocss/vite";
import { defineConfig } from "vite";

// Preview deployments have multiple aliases; derive their origin from each request for CSRF checks.
const vercelOrigin = process.env.VERCEL_ENV === "production" && process.env.VERCEL_PROJECT_PRODUCTION_URL ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}` : undefined;
const netlifyOrigin = process.env.CONTEXT === "production" ? process.env.URL : undefined;
// Prerendered metadata needs an absolute URL without pinning preview requests to one of their aliases.
const prerenderOrigin = process.env.SITE_URL ?? vercelOrigin ?? netlifyOrigin ?? (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : process.env.DEPLOY_PRIME_URL);

export default defineConfig({
  define: { __PRERENDER_ORIGIN__: JSON.stringify(prerenderOrigin ?? "") },
  plugins: [Unocss(), sveltekitOG(), sveltekit({
    preprocess: vitePreprocess(),
    adapter: process.env.VERCEL ? vercel({ runtime: "nodejs24.x" }) : adapter(),
    paths: { origin: process.env.SITE_URL ?? vercelOrigin ?? netlifyOrigin },
    // Keep existing imports while upgrading the framework independently of application syntax.
    alias: { "$lib": "./src/lib", "$py/*": "src/python/*" },
  }), dir2json({ include: ["**/*.py", "**/*.j2", "**/pyproject.toml", "**/README.md"] })],
  assetsInclude: ["src/python/**/*"],
  server: { allowedHosts: true },
  optimizeDeps: {
    entries: [
      "index.html",
      "**/*.svelte",
      "src/routes/**/*.ts",
      "!**/*server.ts",
    ],
  },
});

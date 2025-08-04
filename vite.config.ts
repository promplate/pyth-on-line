import { sveltekit } from "@sveltejs/kit/vite";
import dir2json from "rollup-plugin-flatten-dir";
import Unocss from "unocss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [Unocss(), sveltekit(), dir2json({ include: ["**/*.py", "**/*.j2"] })],
  assetsInclude: ["src/python/**/*"],
  test: {
    include: ["src/**/*.{test,spec}.{js,ts}"],
    environment: "jsdom",
    setupFiles: ["./src/tests/setup.ts"],
    globals: true
  },
});

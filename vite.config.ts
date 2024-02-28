import { sveltekit } from "@sveltejs/kit/vite";
import Unocss from "unocss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [Unocss(), sveltekit()],
});

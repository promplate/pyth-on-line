import dir2json from "./src/lib/plugins/dir2json";
import { sveltekit } from "@sveltejs/kit/vite";
import Unocss from "unocss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [Unocss(), sveltekit(), dir2json({ includes: ["py", "j2"] })],
  assetsInclude: ["src/python/**/*"],
});

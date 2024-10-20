import extractorSvelte from "@unocss/extractor-svelte";
import { defineConfig, presetIcons, presetTypography, presetUno, presetWebFonts, transformerDirectives, transformerVariantGroup } from "unocss";

const config = defineConfig({
  extractors: [extractorSvelte()],
  transformers: [transformerVariantGroup(), transformerDirectives()],
  presets: [presetUno(), presetWebFonts({ provider: "none", fonts: { mono: ["Fira Code Variable", "MiSans"], sans: "MiSans" } }), presetIcons(), presetTypography()],
  shortcuts: {
    "font-sans": "font-sans font-350",
    "not-prose": "font-normal",
  },
});

export default config;

import extractorSvelte from "@unocss/extractor-svelte";
import { defineConfig, presetIcons, presetTypography, presetWebFonts, presetWind3, transformerDirectives, transformerVariantGroup } from "unocss";

const config = defineConfig({
  extractors: [extractorSvelte()],
  transformers: [transformerVariantGroup(), transformerDirectives()],
  presets: [presetWind3({ preflight: "on-demand" }), presetWebFonts({ provider: "none", fonts: { mono: ["Fira Code Variable", "MiSans"], sans: "MiSans" } }), presetIcons(), presetTypography()],
  shortcuts: {
    "font-sans": "font-sans font-350",
    "not-prose": "font-normal",
  },
});

export default config;

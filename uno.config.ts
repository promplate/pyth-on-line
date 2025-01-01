import extractorSvelte from "@unocss/extractor-svelte";
import { defineConfig, presetIcons, presetTypography, presetUno, presetWebFonts, transformerDirectives, transformerVariantGroup } from "unocss";

const config = defineConfig({
  extractors: [extractorSvelte()],
  transformers: [transformerVariantGroup(), transformerDirectives()],
  presets: [presetUno({ preflight: "on-demand" }), presetWebFonts({ provider: "none", fonts: { mono: "Fira Code Variable", sans: "Inter Variable" } }), presetIcons(), presetTypography()],
});

export default config;

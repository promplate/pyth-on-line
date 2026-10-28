import extractorSvelte from "@unocss/extractor-svelte";
import { defineConfig, presetIcons, presetTypography, presetWebFonts, presetWind3, transformerDirectives, transformerVariantGroup } from "unocss";

const typography = presetTypography({
  // Pages can set --un-prose-hr on an ancestor; the preset must not shadow it with its light-theme default.
  colorScheme: { hr: "inherit" },
  // The site's compact, dark Markdown predates the preset's Tailwind defaults. Keep these choices explicit when upgrading the preset.
  cssExtend: {
    "p, ul, ol, pre": { "margin": "1em 0", "line-height": "1.75" },
    "h1, h2, h3, h4, h5, h6": { "line-height": "1.25" },
    "ol, ul": { "padding-inline-start": "1.25em" },
    "li": { margin: "0" },
    "ol > li, ul > li": { "padding-inline-start": "0" },
    // The preset splits selectors at ::, so pseudo-element keys must stay separate.
    "ol > li::marker": { "color": "inherit", "font-weight": "inherit" },
    "ul > li::marker": { color: "inherit" },
    "ul ul, ul ol, ol ul, ol ol": { margin: "1em 0" },
    "hr + *, h2 + *, h3 + *, h4 + *": { "margin-top": "1em" },
    "blockquote": { "margin": "1em 0", "color": "inherit", "font-weight": "inherit" },
    "blockquote p:first-of-type::before": { content: "none" },
    "blockquote p:last-of-type::after": { content: "none" },
    "a": { color: "inherit" },
    "pre": { "color": "inherit", "font-size": "inherit", "background": "transparent" },
    "pre, code": { "word-spacing": "normal", "word-break": "normal", "overflow-wrap": "normal", "tab-size": "4", "hyphens": "none" },
    "table": { "display": "block", "margin": "1em 0", "font-size": "inherit", "line-height": "inherit", "overflow-x": "auto" },
    "thead": { "border-bottom-width": "0" },
    "thead th": { "color": "inherit", "font-weight": "inherit", "vertical-align": "middle" },
    "tbody td": { "vertical-align": "middle" },
    "thead th, tbody td, tfoot td": { padding: ".625em 1em" },
    "thead th:first-child, tbody td:first-child, tfoot td:first-child": { "padding-inline-start": "1em" },
    "thead th:last-child, tbody td:last-child, tfoot td:last-child": { "padding-inline-end": "1em" },
    "img, video": { "margin": "0", "max-width": "100%" },
    "figure, picture": { margin: "1em 0" },
    "figcaption": { "color": "inherit", "margin-top": "0", "line-height": "inherit" },
    "hr": { margin: "2em 0", border: "1px solid var(--un-prose-hr, #ffffff20)" },
  },
});

const config = defineConfig({
  extractors: [extractorSvelte()],
  transformers: [transformerVariantGroup(), transformerDirectives()],
  presets: [presetWind3({ preflight: "on-demand" }), presetWebFonts({ provider: "none", fonts: { mono: "Fira Code Variable", jb: ["JetBrains Mono Variable", "monospace"], sans: "Inter Variable" } }), presetIcons(), typography],
  shortcuts: {
    row: "flex flex-row",
    col: "flex flex-col",
  },
});

export default config;

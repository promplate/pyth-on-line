import type { ShikiTransformer } from "shiki";

import { cacheGlobally } from "./utils/cache";
import { bundledLanguages, bundledThemes, createHighlighter } from "shiki";

const languages = Object.keys(bundledLanguages);

export async function getHighlighter(lang: string) {
  if (!languages.includes(lang) && lang !== "text") {
    console.error(`Language "${lang}" is not supported by Shiki.`);
    lang = "text";
  }
  return await cacheGlobally(`shiki-${lang}`, async () => {
    const { default: theme } = await bundledThemes["vitesse-dark"]();
    const tokenColors = [...(theme.tokenColors ?? []), { scope: ["comment", "punctuation.definition.comment", "string.comment"], settings: { foreground: "#758575" } }];
    return await createHighlighter({ themes: [{ ...theme, tokenColors }], langs: [lang] });
  })();
}

const transformers: ShikiTransformer[] = [
  { pre: (node) => { node.properties.tabindex = "-1"; } },
];

export async function highlight(lang = "text", code: string) {
  return (await getHighlighter(lang)).codeToHtml(code, { lang, theme: "vitesse-dark", transformers });
}

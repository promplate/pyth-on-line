import type { ShikiTransformer } from "shiki";

import { cacheGlobally } from "./utils/cache";
import { bundledLanguages, createHighlighter } from "shiki";

export const languages = Object.keys(bundledLanguages);

export async function getHighlighter(lang: string) {
  // Normalize language to lowercase for consistency with bundledLanguages
  const normalizedLang = lang.toLowerCase();

  if (!languages.includes(normalizedLang) && normalizedLang !== "text") {
    console.error(`Language "${lang}" is not supported by Shiki.`);
    lang = "text";
  }
  else {
    lang = normalizedLang;
  }

  return await cacheGlobally(`shiki-${lang}`, async () => {
    return await createHighlighter({ themes: ["vitesse-dark"], langs: [lang] });
  })();
}

const transformers: ShikiTransformer[] = [
  { pre: (node) => { node.properties.tabindex = "-1"; } },
];

export async function highlight(lang = "text", code: string) {
  // Normalize language to lowercase for consistency
  const normalizedLang = lang.toLowerCase();
  return (await getHighlighter(normalizedLang)).codeToHtml(code, { lang: normalizedLang, theme: "vitesse-dark", transformers });
}

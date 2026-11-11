import type { ShikiTransformer } from "shiki";

import { cacheGlobally } from "./utils/cache";
import { bundledLanguages, createHighlighter, isSpecialLang } from "shiki";

const languages = Object.keys(bundledLanguages);

export async function getHighlighter(lang: string) {
  if (!languages.includes(lang) && !isSpecialLang(lang)) {
    console.error(`Language "${lang}" is not supported by Shiki.`);
    lang = "text";
  }
  return await cacheGlobally(`shiki-${lang}`, async () => {
    return await createHighlighter({ themes: ["vitesse-dark"], langs: [lang] });
  })();
}

const transformers: ShikiTransformer[] = [
  { pre: (node) => { node.properties.tabindex = "-1"; } },
];

export async function highlight(lang = "text", code: string) {
  if (!languages.includes(lang) && !isSpecialLang(lang)) {
    lang = "text";
  }
  return (await getHighlighter(lang)).codeToHtml(code, { lang, theme: "vitesse-dark", transformers });
}

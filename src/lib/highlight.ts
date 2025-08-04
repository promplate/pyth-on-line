import type { ShikiTransformer } from "shiki";

import { cacheGlobally } from "./utils/cache";
import { bundledLanguages, createHighlighter } from "shiki";

export const languages = Object.keys(bundledLanguages);

export async function getHighlighter(lang: string) {
  if (!languages.includes(lang) && lang !== "text") {
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

const interactiveTransformers: ShikiTransformer[] = [
  { pre: (node) => { node.properties.tabindex = "-1"; } },
  {
    // Add data-variable attributes to Python identifiers that could be inspected
    span: (node, line, col, hast) => {
      if (hast?.options?.lang === "python") {
        // Check if this is likely a variable name
        const text = node.children?.[0]?.type === "text" ? node.children[0].value : "";
        
        if (text && typeof text === "string" && /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(text)) {
          // Add data attributes for inspection
          node.properties = node.properties || {};
          node.properties["data-variable"] = text;
          node.properties["data-inspectable"] = "true";
        }
      }
    }
  }
];

export async function highlight(lang = "text", code: string, interactive = false) {
  const usedTransformers = interactive ? interactiveTransformers : transformers;
  return (await getHighlighter(lang)).codeToHtml(code, { lang, theme: "vitesse-dark", transformers: usedTransformers });
}

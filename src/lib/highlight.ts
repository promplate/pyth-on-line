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
      if (hast?.options?.lang === "python" && node.properties.class?.includes("token-keyword-flow") === false) {
        const classes = Array.isArray(node.properties.class) ? node.properties.class : [node.properties.class].filter(Boolean);
        const tokenTypes = classes.join(" ");
        
        // Check if this is likely a variable (identifier that's not a keyword)
        if (tokenTypes.includes("variable") || 
            (tokenTypes.includes("entity") && tokenTypes.includes("name")) ||
            (!tokenTypes.includes("keyword") && !tokenTypes.includes("string") && 
             !tokenTypes.includes("comment") && !tokenTypes.includes("number") &&
             node.children?.[0]?.type === "text" && /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(node.children[0].value as string))) {
          
          const varName = node.children?.[0]?.type === "text" ? node.children[0].value : "";
          if (varName && typeof varName === "string" && varName.length > 0) {
            node.properties["data-variable"] = varName;
            node.properties["data-inspectable"] = "true";
          }
        }
      }
    }
  }
];

export async function highlight(lang = "text", code: string, interactive = false) {
  const usedTransformers = interactive ? interactiveTransformers : transformers;
  return (await getHighlighter(lang)).codeToHtml(code, { lang, theme: "vitesse-dark", transformers: usedTransformers });
}

import type { ShikiTransformer } from "shiki";

import { cacheGlobally } from "./utils/cache";
import { createHighlighter } from "shiki";

export async function getHighlighter(lang: string) {
  return await cacheGlobally(`shiki-${lang}`, async () => {
    try {
      return await createHighlighter({ themes: ["vitesse-dark"], langs: [lang] });
    }
    catch {
      // `bundledLanguages` eagerly pulls every grammar into SSR bundles.
      if (lang !== "text") {
        console.error(`Language "${lang}" is not supported by Shiki.`);
        return await createHighlighter({ themes: ["vitesse-dark"], langs: ["text"] });
      }
      throw new Error("Failed to initialize Shiki highlighter.");
    }
  })();
}

const transformers: ShikiTransformer[] = [
  { pre: (node) => { node.properties.tabindex = "-1"; } },
];

export async function highlight(lang = "text", code: string) {
  return (await getHighlighter(lang)).codeToHtml(code, { lang, theme: "vitesse-dark", transformers });
}

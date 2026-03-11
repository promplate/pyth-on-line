import type { LanguageInput, ShikiTransformer } from "shiki";

import vitesseDark from "@shikijs/themes/vitesse-dark";
import { cacheGlobally } from "./utils/cache";
import { createHighlighterCore } from "shiki/core";
import { createJavaScriptRegexEngine } from "shiki/engine/javascript";

const aliases: Record<string, string> = {
  js: "javascript",
  ts: "typescript",
  py: "python",
  md: "markdown",
  yml: "yaml",
  sh: "bash",
  shell: "bash",
  txt: "markdown",
  plaintext: "markdown",
  text: "markdown",
};

const langLoaders: Record<string, () => Promise<{ default: LanguageInput }>> = {
  python: () => import("@shikijs/langs/python"),
  javascript: () => import("@shikijs/langs/javascript"),
  typescript: () => import("@shikijs/langs/typescript"),
  json: () => import("@shikijs/langs/json"),
  markdown: () => import("@shikijs/langs/markdown"),
  html: () => import("@shikijs/langs/html"),
  css: () => import("@shikijs/langs/css"),
  bash: () => import("@shikijs/langs/bash"),
  yaml: () => import("@shikijs/langs/yaml"),
  toml: () => import("@shikijs/langs/toml"),
};

async function getLanguage(lang: string) {
  const normalized = aliases[lang] ?? lang;
  const load = langLoaders[normalized] ?? langLoaders.markdown;

  if (!langLoaders[normalized]) {
    console.error(`Language "${lang}" is not supported by Shiki.`);
  }

  const definition = (await load()).default;
  return { normalized: definition.name, definition };
}

export async function getHighlighter(lang: string) {
  const { normalized, definition } = await getLanguage(lang);

  return await cacheGlobally(`shiki-${normalized}`, async () => {
    return await createHighlighterCore({
      engine: createJavaScriptRegexEngine(),
      themes: [vitesseDark],
      langs: [definition],
    });
  })();
}

const transformers: ShikiTransformer[] = [
  { pre: (node) => { node.properties.tabindex = "-1"; } },
];

export async function highlight(lang = "text", code: string) {
  const { normalized } = await getLanguage(lang);
  return (await getHighlighter(normalized)).codeToHtml(code, {
    lang: normalized,
    theme: vitesseDark.name,
    transformers,
  });
}

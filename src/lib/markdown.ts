import type { BuiltinLanguage } from "shiki";

import { cacheGlobally } from "./utils/cache";
import rehypeShiki from "@shikijs/rehype";
import { fromMarkdown } from "mdast-util-from-markdown";
import { gfmFromMarkdown } from "mdast-util-gfm";
import { gfm } from "micromark-extension-gfm";
import rehypeStringify from "rehype-stringify";
import remarkRehype from "remark-rehype";
import { unified } from "unified";

async function getProcessor(langs: BuiltinLanguage[] = []) {
  return unified().use(remarkRehype).use(rehypeShiki, { theme: "vitesse-dark", langs }).use(rehypeStringify);
}

export async function renderMarkdown(text: string, langs: BuiltinLanguage[] = []) {
  const processor = await cacheGlobally(`md-${langs.join()}`, getProcessor.bind(null, langs))();

  // Parse markdown with micromark and convert to mdast
  const mdast = fromMarkdown(text, {
    extensions: [gfm()],
    mdastExtensions: [gfmFromMarkdown()],
  });

  const transformedAst = await processor.run(mdast);
  const value = processor.stringify(transformedAst);
  return String(value);
};

export async function md(strings: TemplateStringsArray, ...values: any[]) {
  const text = strings.reduce((result, str, index) => {
    return result + str + (index < values.length ? values[index] : "");
  }, "");
  return await renderMarkdown(text);
}

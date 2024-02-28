import type { BuiltinLanguage } from "shiki";

import { cacheGlobally } from "./utils/cache";
import rehypeShiki from "@shikijs/rehype";
import rehypeStringify from "rehype-stringify";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import { unified } from "unified";

async function getProcessor(langs: BuiltinLanguage[] = []) {
  return unified().use(remarkParse).use(remarkRehype).use(rehypeShiki, { theme: "vitesse-dark", langs }).use(rehypeStringify);
}

export async function renderMarkdown(text: string, langs: BuiltinLanguage[] = []) {
  const processor = await cacheGlobally(`md-${langs.join()}`, getProcessor.bind(null, langs))();
  const { value } = await processor.process(text);
  return value as string;
};

export async function md(strings: TemplateStringsArray, ...values: any[]) {
  const text = strings.reduce((result, str, index) => {
    return result + str + (index < values.length ? values[index] : "");
  }, "");
  return await renderMarkdown(text);
}

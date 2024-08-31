import rehypeParse from "rehype-parse";
import rehypeRemark from "rehype-remark";
import remarkStringify from "remark-stringify";
import TurndownService from "turndown";
// @ts-expect-error missing types
import { gfm, strikethrough, tables } from "turndown-plugin-gfm";
import { unified } from "unified";

const processor = unified().use(rehypeParse).use(rehypeRemark).use(remarkStringify);

export function html2markdown(html: string) {
  try {
    return String(processor.processSync(html));
  }
  catch {
    const markdown = new TurndownService({ codeBlockStyle: "fenced" }).use(gfm).use(tables).use(strikethrough);
    return markdown.turndown(html);
  }
}

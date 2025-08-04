import { fromHtml } from "hast-util-from-html";
import { toMdast } from "hast-util-to-mdast";
import { toMarkdown } from "mdast-util-to-markdown";
import TurndownService from "turndown";
// @ts-expect-error missing types
import { gfm, strikethrough, tables } from "turndown-plugin-gfm";

export function html2markdown(html: string) {
  try {
    // Parse HTML to hast
    const hast = fromHtml(html);

    // Convert hast to mdast
    const mdast = toMdast(hast);

    // Convert mdast to markdown string
    return toMarkdown(mdast);
  }
  catch {
    const markdown = new TurndownService({ codeBlockStyle: "fenced" }).use(gfm).use(tables).use(strikethrough);
    return markdown.turndown(html);
  }
}

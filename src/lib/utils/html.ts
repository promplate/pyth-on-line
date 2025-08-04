// @ts-expect-error missing types
import { gfm } from "@joplin/turndown-plugin-gfm";
import { fromHtml } from "hast-util-from-html";
import { toMdast } from "hast-util-to-mdast";
import { toMarkdown } from "mdast-util-to-markdown";
import TurndownService from "turndown";

export function html2markdown(html: string) {
  try {
    const hast = fromHtml(html);
    const tree = toMdast(hast);
    return toMarkdown(tree);
  }
  catch {
    const markdown = new TurndownService({ codeBlockStyle: "fenced" }).use(gfm);
    return markdown.turndown(html);
  }
}

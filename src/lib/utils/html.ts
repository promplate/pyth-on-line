// @ts-expect-error missing types
import { gfm } from "@joplin/turndown-plugin-gfm";
import TurndownService from "turndown";

const markdown = new TurndownService({ codeBlockStyle: "fenced" }).use(gfm);

export function html2markdown(html: string) {
  return markdown.turndown(html);
}

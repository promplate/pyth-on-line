import { Readability } from "@mozilla/readability";
import { JSDOM } from "jsdom";
import rehypeParse from "rehype-parse";
import rehypeRemark from "rehype-remark";
import remarkStringify from "remark-stringify";
import TurndownService from "turndown";
// @ts-expect-error missing types
import { gfm, strikethrough, tables } from "turndown-plugin-gfm";
import { unified } from "unified";

const processor = unified().use(rehypeParse).use(rehypeRemark).use(remarkStringify);

/**
 * Extract main content from HTML using Mozilla Readability
 * @param html The HTML string to process
 * @returns The extracted main content HTML or original HTML if extraction fails
 */
function extractMainContent(html: string): string {
  try {
    // Create a virtual DOM using JSDOM
    const dom = new JSDOM(html, { url: "https://example.com" });

    // Use Mozilla Readability to extract the main content
    const reader = new Readability(dom.window.document);
    const article = reader.parse();

    // Return the extracted content or fall back to original HTML
    return article?.content || html;
  }
  catch {
    // If Readability fails, return the original HTML
    return html;
  }
}

export function html2markdown(html: string) {
  // First, extract the main content using Mozilla Readability
  const cleanedHtml = extractMainContent(html);

  try {
    return String(processor.processSync(cleanedHtml));
  }
  catch {
    const markdown = new TurndownService({ codeBlockStyle: "fenced" }).use(gfm).use(tables).use(strikethrough);
    return markdown.turndown(cleanedHtml);
  }
}

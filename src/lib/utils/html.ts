import rehypeParse from "rehype-parse";
import rehypeRemark from "rehype-remark";
import remarkStringify from "remark-stringify";
import { unified } from "unified";

const processor = unified().use(rehypeParse).use(rehypeRemark).use(remarkStringify);

export function html2markdown(html: string) {
  return String(processor.processSync(html));
}

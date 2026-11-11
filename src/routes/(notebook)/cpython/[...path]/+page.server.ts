import type { PageServerLoad } from "./$types";
import type { Node, Nodes } from "mdast";

import { error } from "@sveltejs/kit";
import { load as parse } from "cheerio";
import { fromHtml } from "hast-util-from-html";
import { toMdast } from "hast-util-to-mdast";

declare module "mdast" {
  interface RootContentMap {
    anchor: Node & { type: "anchor" };
  }
  interface PhrasingContentMap {
    anchor: RootContentMap["anchor"];
  }
}

function prepareForRendering(node: Nodes) {
  delete node.position;
  // Keep anchors out of paragraph wrapping during conversion, then render them as spans.
  if (node.type === "anchor")
    node.data!.hName = "span";
  if ("children" in node) {
    // Section anchors must not replace the heading as the article's first child.
    for (let i = node.children.length - 2; i >= 0; i--) {
      const anchor = node.children[i];
      const next = node.children[i + 1];
      if (anchor.type === "anchor" && next.type === "heading") {
        next.children.unshift(anchor);
        node.children.splice(i, 1);
      }
    }
    node.children.forEach(prepareForRendering);
  }
}

export const load: PageServerLoad = async ({ params: { path }, fetch, url }) => {
  const res = await fetch(`https://docs.python.org/3.14/${path}`, { credentials: "omit" }).catch(() => error(502, "Unable to load documentation"));
  if (!res.ok)
    error(res.status === 404 ? 404 : 502, res.status === 404 ? "Documentation not found" : "Unable to load documentation");
  const html = await res.text().catch(() => error(502, "Unable to load documentation"));
  const $ = parse(html);
  const body = $("div.body");
  if (body.length !== 1)
    error(502, "Unable to load documentation");
  const base = new URL(path.endsWith(".html") ? url.pathname : `${url.pathname.replace(/\/$/, "")}/`, url);
  body.find("a.headerlink").remove();
  body.find("a[href], img[src]").each((_, element) => {
    const attribute = element.tagName === "a" ? "href" : "src";
    $(element).attr(attribute, new URL($(element).attr(attribute)!, base).href);
  });
  body.find("[id]").each((_, element) => {
    const code = $(element).closest("pre")[0] ?? $(element).closest("code")[0];
    const anchor = $("<notebook-anchor>").attr("id", $(element).attr("id")!);
    if (code)
      $(code).before(anchor);
    else
      $(element).prepend(anchor);
  });
  const node = toMdast(fromHtml(body.html()!), {
    handlers: {
      "notebook-anchor": (_, element) => ({ type: "anchor", data: { hProperties: { id: element.properties.id } } }),
    },
  });
  prepareForRendering(node);
  return { node, title: $("title").text() };
};

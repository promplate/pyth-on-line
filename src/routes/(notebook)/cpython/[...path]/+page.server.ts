import type { PageServerLoad } from "./$types";

import { error } from "@sveltejs/kit";
import { html2markdown } from "#lib/utils/html.js";
import { load as parse } from "cheerio";

export const load: PageServerLoad = async ({ params: { path }, fetch, url }) => {
  const res = await fetch(`https://docs.python.org/3.14/${path}`, { credentials: "omit" }).catch(() => error(502, "Unable to load documentation"));
  if (!res.ok)
    error(res.status === 404 ? 404 : 502, res.status === 404 ? "Documentation not found" : "Unable to load documentation");
  const html = await res.text().catch(() => error(502, "Unable to load documentation"));
  const $ = parse(html);
  const body = $("div.body");
  const base = new URL(path.endsWith(".html") ? url.pathname : `${url.pathname.replace(/\/$/, "")}/`, url);
  body.find("a.headerlink").remove();
  body.find("a[href], img[src]").each((_, element) => {
    const attribute = element.tagName === "a" ? "href" : "src";
    $(element).attr(attribute, new URL($(element).attr(attribute)!, base).href);
  });
  return { text: html2markdown(body.html()!).replaceAll("¶", ""), title: $("title").text() };
};

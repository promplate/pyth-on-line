import type { PageServerLoad } from "./$types";

import { error } from "@sveltejs/kit";
import { load as parse } from "cheerio";

export const load: PageServerLoad = async ({ params: { path }, fetch }) => {
  const res = await fetch(`https://docs.python.org/3.14/${path}`, { credentials: "omit" });
  if (!res.ok)
    error(res.status === 404 ? 404 : 502, res.status === 404 ? "Documentation not found" : "Unable to load documentation");
  const html = await res.text();
  return { html, title: parse(html)("title").text() };
};

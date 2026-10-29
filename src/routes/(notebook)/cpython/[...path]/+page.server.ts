import type { PageServerLoad } from "./$types";

import { load as parse } from "cheerio";

export const load: PageServerLoad = async ({ params: { path }, fetch }) => {
  const res = await fetch(`https://docs.python.org/3.14/${path}`, { credentials: "omit" });
  const html = await res.text();
  return { html, title: parse(html)("title").text() };
};

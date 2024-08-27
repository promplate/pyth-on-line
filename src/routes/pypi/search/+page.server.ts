import type { PageServerLoad } from "./$types";

import { load as loadCheerio } from "cheerio";
import { parseDocument } from "htmlparser2";

export const load = (async ({ fetch, url: { searchParams } }) => {
  const query = searchParams.get("q") ?? "promplate";
  const page = searchParams.get("page") ?? "1";

  const res = await fetch(`https://pypi.org/search/?q=${query}&page=${page}`).then(r => r.text());

  const $ = loadCheerio(parseDocument(res));

  const total = Number($("form > div p > strong").text().replaceAll(",", ""));

  const npages = $(".button-group--pagination a").eq(-2).text();

  const results = $("a.package-snippet").map((_, el) => {
    const { href } = el.attribs;
    const [name, version] = $("h3 > span", el).map((_, el) => $(el).text()).toArray();
    const description = $("p", el).text().trim();
    const updated = $("time", el).text().trim();
    return { href, name, version, description, updated };
  }).toArray();

  return { total, page, npages, results };
}) satisfies PageServerLoad;

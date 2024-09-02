import type { RequestEvent } from "./$types";

import { load as loadCheerio } from "cheerio";
import { parseDocument } from "htmlparser2";

export async function search({ fetch, url: { searchParams } }: RequestEvent) {
  const query = searchParams.get("q");
  if (!query) {
    return { query, total: null, page: 0, npages: 0, results: [] };
  }
  const page = Number(searchParams.get("page") ?? "1");

  const res = await fetch(`https://pypi.org/search/?q=${query}&page=${page}`).then(r => r.text());

  const $ = loadCheerio(parseDocument(res));

  const total = Number($("form > div p > strong").text().replaceAll(",", ""));

  const npages = Number($(".button-group--pagination a").eq(-2).text());

  const results = $("a.package-snippet").map((_, el) => {
    const [name, version] = $("h3 > span", el).map((_, el) => $(el).text()).toArray();
    let description: string | undefined = $("p", el).text().trim();
    if (description === "None")
      description = undefined;
    const updated = $("time", el).text().trim();
    return { name, version, description, updated };
  }).toArray();

  return { query, total, page, npages, results };
}

import type { LibrariesIO } from "libraries.io";

import * as env from "$env/static/private";

// eslint-disable-next-line ts/ban-ts-comment
// @ts-ignore
const apiKey = env.LIBRARIES_IO_API_KEY;

export async function search(query: string, page = 1, per_page = 30) {
  const url = new URL("https://libraries.io/api/search");
  url.searchParams.append("q", query);
  url.searchParams.append("page", page.toString());
  url.searchParams.append("per_page", per_page.toString());
  url.searchParams.append("api_key", apiKey);
  url.searchParams.append("platforms", "pypi");
  url.searchParams.append("sort", "rank");
  return await fetch(url).then(async (res) => {
    const total = Number(res.headers.get("total"));
    return { total, data: await res.json() as Awaited<ReturnType<LibrariesIO["api"]["project"]["search"]>>["data"] };
  });
}

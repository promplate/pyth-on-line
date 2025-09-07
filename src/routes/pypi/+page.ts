import type { search } from "./~search/search";
import type { PageLoad } from "./$types";

export const load = (async ({ url, fetch }) => {
  const query = url.searchParams.get("q");
  if (!query) {
    return { query, total: null, page: 0, npages: 0, results: [] };
  }
  const searchUrl = new URL(`${url.pathname}/~search${url.search}`, url);
  return await fetch(searchUrl).then(res => res.json()) as ReturnType<typeof search>;
}) satisfies PageLoad;

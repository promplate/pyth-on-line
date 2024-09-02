import type { PageLoad } from "./$types";
import type { search } from "./search";

export const load = (async (event) => {
  const query = event.url.searchParams.get("q");
  if (!query) {
    return { query, total: null, page: 0, npages: 0, results: [] };
  }
  return await event.fetch(event.url).then(res => res.json()) as ReturnType<typeof search>;
}) satisfies PageLoad;

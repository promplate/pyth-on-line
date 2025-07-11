import type { RequestEvent } from "./$types";

import { search as searchPypi } from "$lib/libraries.io/client";

export async function search({ url: { searchParams } }: RequestEvent) {
  const query = searchParams.get("q");
  if (!query) {
    return { query, total: null, page: 0, npages: 0, results: [] };
  }
  const page = Number(searchParams.get("page") ?? "1");
  const per_page = 30;

  const { data, total } = await searchPypi(query, page, per_page);

  const results = data.map(item => ({
    name: item.name,
    version: item.versions.at(-1)?.number,
    description: item.description,
    updated: new Date(item.latest_release_published_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }),
  }));

  return { query, total, page, npages: Math.ceil(total / per_page), results };
}

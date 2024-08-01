import type { PageLoad } from "./$types";

import { type GistResponse, transformFiles } from "./common";

export const load = (async ({ params: { gist_id }, fetch }) => {
  const { files }: GistResponse = await fetch(`https://api.github.com/gists/${gist_id}`).then(res => res.json());
  return { sources: transformFiles(files) };
}) satisfies PageLoad;

import type { PageServerLoad } from "./$types";

import { type GistResponse, transformFiles } from "./common";
import { env } from "$env/dynamic/private";

const headers = new Headers();

if (env.GITHUB_TOKEN)
  headers.set("Authorization", `Bearer ${env.GITHUB_TOKEN}`);

export const load = (async ({ params: { gist_id }, fetch }) => {
  const { files }: GistResponse = await fetch(`https://api.github.com/gists/${gist_id}`, { headers }).then(res => res.json());
  return { sources: transformFiles(files) };
}) satisfies PageServerLoad;

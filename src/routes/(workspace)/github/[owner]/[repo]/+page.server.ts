import type { PageServerLoad } from "./$types";

import { error } from "@sveltejs/kit";
import * as env from "$app/env/private";
import { unzip } from "unzipit";

async function getRepoFiles(repo: string, access_token = env.GITHUB_TOKEN): Promise<{ [path: string]: string }> {
  const url = `https://api.github.com/repos/${repo}/zipball`;

  const res = await fetch(url, access_token ? { headers: { Authorization: `Bearer ${access_token}` } } : undefined).catch(() => error(502, "Unable to load repository"));
  if (!res.ok)
    error(res.status === 404 ? 404 : 502, res.status === 404 ? "Repository not found" : "Unable to load repository");
  const { entries } = await unzip(await res.arrayBuffer().catch(() => error(502, "Unable to load repository")));
  return Object.fromEntries(
    await Promise.all(
      Object.entries(entries).filter(([_, entry]) => !entry.isDirectory).map(async ([path, entry]) => [path.slice(path.indexOf("/") + 1), await entry.text()]),
    ),
  );
}

export const load = (async ({ params: { owner, repo }, cookies }) => {
  const access_token = cookies.get("access_token");
  const sources = await getRepoFiles(`${owner}/${repo}`, access_token);
  return { sources };
}) satisfies PageServerLoad;

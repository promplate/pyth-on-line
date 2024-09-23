import type { PageServerLoad } from "./$types";

import { env } from "$env/dynamic/private";
import { unzip } from "unzipit";

async function getRepoFiles(repo: string, access_token = env.GITHUB_TOKEN): Promise<{ [path: string]: string }> {
  const url = `https://api.github.com/repos/${repo}/zipball`;

  const { entries } = await unzip(
    access_token ? await fetch(url, { headers: { Authorization: `Bearer ${access_token}` } }).then(res => res.arrayBuffer()) : url,
  );
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

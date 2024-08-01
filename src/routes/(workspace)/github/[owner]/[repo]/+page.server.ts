import type { PageServerLoad } from "./$types";

import { env } from "$env/dynamic/private";
import { unzip } from "unzipit";

async function getRepoFiles(repo: string): Promise<{ [path: string]: string }> {
  const url = `https://api.github.com/repos/${repo}/zipball`;

  const { entries } = await unzip(
    env.GITHUB_TOKEN ? await fetch(url, { headers: { Authorization: `Bearer ${env.GITHUB_TOKEN}` } }).then(res => res.arrayBuffer()) : url,
  );
  return Object.fromEntries(
    await Promise.all(
      Object.entries(entries).filter(([_, entry]) => !entry.isDirectory).map(async ([path, entry]) => [path.slice(path.indexOf("/") + 1), await entry.text()]),
    ),
  );
}

export const load = (async ({ params: { owner, repo } }) => {
  const sources = await getRepoFiles(`${owner}/${repo}`);
  return { sources };
}) satisfies PageServerLoad;

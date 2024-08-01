import type { PageServerLoad } from "./$types";

import { unzip } from "unzipit";

async function getRepoFiles(repo: string): Promise<{ [path: string]: string }> {
  const { entries } = await unzip(`https://api.github.com/repos/${repo}/zipball`);
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

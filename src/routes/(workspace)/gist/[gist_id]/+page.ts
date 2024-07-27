import type { PageLoad } from "./$types";

interface GistResponse {
  files: {
    [filename: string]: {
      content: string;
    };
  };
};

export const load = (async ({ params: { gist_id }, fetch }) => {
  const { files }: GistResponse = await fetch(`https://api.github.com/gists/${gist_id}`).then(res => res.json());
  return { sources: Object.fromEntries(Object.entries(files).map(([filename, { content }]) => [filename, content])) };
}) satisfies PageLoad;

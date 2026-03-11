import type { PageLoad } from "./$types";

export const ssr = false;

export const load: PageLoad = async ({ params: { path }, fetch }) => {
  const target = `https://docs.python.org/3.13/${path}`;
  const html = await fetch(`/proxy?url=${encodeURIComponent(target)}`).then(r => r.text());
  return { html };
};

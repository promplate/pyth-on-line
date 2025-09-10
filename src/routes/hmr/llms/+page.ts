import type { PageLoad } from "./$types";

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
  return { html: fetch("/hmr/llms.txt", { headers: { "content-type": "text/markdown" } }).then(r => r.text()) };
};

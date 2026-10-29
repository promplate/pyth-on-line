import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async ({ params: { path }, fetch }) => {
  const res = await fetch(`https://docs.python.org/3.14/${path}`, { credentials: "omit" });
  return { html: await res.text() };
};

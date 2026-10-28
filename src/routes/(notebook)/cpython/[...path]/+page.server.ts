import type { PageServerLoad } from "./$types";

import { forwardFetch } from "#lib/utils/headers.js";

export const load: PageServerLoad = async ({ params: { path }, request }) => {
  const res = await forwardFetch(`https://docs.python.org/3.14/${path}`, request);
  return { html: await res.text() };
};

import type { PageServerLoad } from "./$types";

import { forwardFetch } from "$lib/utils/headers";

export const load: PageServerLoad = async ({ params: { path }, request }) => {
  const res = await forwardFetch(`https://docs.python.org/3.12/${path}`, request);
  return { html: await res.text() };
};

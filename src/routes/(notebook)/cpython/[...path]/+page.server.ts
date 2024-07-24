import type { PageServerLoad } from "./$types";

import { get } from "$lib/utils/headers";

export const load: PageServerLoad = async ({ params: { path }, request: { headers } }) => {
  const res = await get(`https://docs.python.org/3.12/${path}`, headers);
  return { html: await res.text() };
};

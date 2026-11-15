import type { PageLoad } from "./$types";

import { redirect } from "@sveltejs/kit";

export const load: PageLoad = ({ url }) => {
  const repo = url.searchParams.get("repo");
  if (repo && /^[^/]+\/[^/]+$/.test(repo))
    redirect(303, `/github/${repo.split("/").map(encodeURIComponent).join("/")}`);
};

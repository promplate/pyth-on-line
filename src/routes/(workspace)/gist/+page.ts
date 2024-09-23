import type { GistMetadata } from "./+server.ts";
import type { PageLoad } from "./$types";

import { redirect } from "@sveltejs/kit";

export const load = (async ({ fetch }) => {
  const res = await fetch("");
  if (res.status === 401) {
    redirect(307, "/oauth");
  }

  return (await res.json()) as { name: string | null; login: string; avatarUrl: string;total: number; gists: GistMetadata[] };
}) satisfies PageLoad;

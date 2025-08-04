import type { GistMetadata } from "./+server.ts";
import type { PageLoad } from "./$types";

import { redirect } from "@sveltejs/kit";
import { userGitHubToken } from "$lib/user-token";
import { get } from "svelte/store";

export const load = (async ({ fetch }) => {
  // Get user token from store
  const token = get(userGitHubToken);

  // Build URL with token if available
  const url = token ? `?token=${encodeURIComponent(token)}` : "";

  const res = await fetch(url);

  if (res.status === 401) {
    // If user token failed, try without it (fall back to OAuth)
    if (token) {
      const fallbackRes = await fetch("");
      if (fallbackRes.status === 401) {
        redirect(307, "/oauth");
      }
      return (await fallbackRes.json()) as { name: string | null; login: string; avatarUrl: string; total: number; gists: GistMetadata[] };
    }
    else {
      redirect(307, "/oauth");
    }
  }

  return (await res.json()) as { name: string | null; login: string; avatarUrl: string; total: number; gists: GistMetadata[] };
}) satisfies PageLoad;

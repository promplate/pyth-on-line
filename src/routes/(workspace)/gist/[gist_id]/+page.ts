import type { PageLoad } from "./$types";

import { error } from "@sveltejs/kit";
import { userGitHubToken } from "$lib/user-token";
import { get } from "svelte/store";

export const load = (async ({ fetch }) => {
  // Get user token from store
  const token = get(userGitHubToken);

  // Build URL with token if available
  const url = token ? `?token=${encodeURIComponent(token)}` : "";

  const res = await fetch(url);

  if (!res.ok) {
    // If user token failed and we have one, try without it
    if (token && res.status === 404) {
      const fallbackRes = await fetch("");
      if (fallbackRes.ok) {
        const sources: Record<string, string> = await fallbackRes.json();
        return { sources };
      }
    }

    // If still failing, throw an appropriate error
    if (res.status === 404) {
      error(404, "Gist not found or not accessible with current permissions");
    }
    else if (res.status === 403) {
      error(403, "Access forbidden. This may be a private gist that requires a personal access token.");
    }
    else {
      error(res.status, "Failed to fetch gist");
    }
  }

  const sources: Record<string, string> = await res.json();
  return { sources };
}) satisfies PageLoad;

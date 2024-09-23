import * as env from "$env/static/public";
import { persisted } from "svelte-persisted-store";
import { derived, readable } from "svelte/store";

// eslint-disable-next-line ts/ban-ts-comment
// @ts-ignore
const client_id = env.PUBLIC_GITHUB_CLIENT_ID;

const SCOPES = "read:user,read:org,repo";

export function login() {
  if (!client_id)
    return;

  sessionStorage.setItem("continue", location.href);
  const url = new URL("https://github.com/login/oauth/authorize");
  url.searchParams.set("client_id", client_id);
  url.searchParams.set("redirect_uri", new URL("/oauth", location.origin).href);
  url.searchParams.set("scope", SCOPES);
  location.replace(url.href);
}

export const accessToken = persisted<string | undefined>(`gh-${SCOPES}`, undefined);

export const canLogin = client_id ? derived(accessToken, $accessToken => !$accessToken) : readable(false);

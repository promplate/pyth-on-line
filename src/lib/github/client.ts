import { accessToken } from "$lib/oauth";
import { get } from "svelte/store";

export async function gql(query: string, token?: string) {
  const { errors, data } = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: {
      "authorization": `Bearer ${token ?? get(accessToken)}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({ query }),
  }).then(res => res.json());
  if (errors) {
    // eslint-disable-next-line no-console
    console.table(errors);
    throw errors;
  }
  else {
    return data;
  }
}

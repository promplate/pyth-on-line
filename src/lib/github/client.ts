import { accessToken } from "#lib/oauth.js";

export async function gql(query: string, token?: string) {
  const { errors, data } = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: {
      "authorization": `Bearer ${token ?? accessToken.current}`,
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

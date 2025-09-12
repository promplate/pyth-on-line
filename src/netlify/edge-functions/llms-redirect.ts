import type { Config } from "@netlify/edge-functions";

export default async () => Response.redirect("/hmr/llms", 302);

export const config: Config = {
  path: "/hmr/llms*",
  excludedPath: "/hmr/llms",
  header: { accept: "text/html" },
};

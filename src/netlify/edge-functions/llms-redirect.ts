import type { Config, Context } from "@netlify/edge-functions";

import { isAIBot } from "ua-parser-js/helpers";

export default async (request: Request, context: Context) => {
  const userAgent = request.headers.get("user-agent") || "";
  if (isAIBot(userAgent)) {
    const res = await context.next();
    res.headers.set("content-type", "text/markdown; charset=utf-8");
    return res;
  }
  else {
    return Response.redirect("/hmr/llms", 302);
  }
};

export const config: Config = {
  path: "/hmr/llms*",
  excludedPath: "/hmr/llms",
  header: { accept: "text/html" },
};

import type { Config, Context } from "@netlify/edge-functions";

import { UAParser } from "ua-parser-js";
import { isBot } from "ua-parser-js/helpers";

export default async (request: Request, context: Context) => {
  const userAgent = request.headers.get("user-agent") || "";
  const parser = new UAParser(userAgent);
  const deviceType = parser.getDevice().type;

  if (isBot(userAgent) || deviceType !== "mobile") {
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

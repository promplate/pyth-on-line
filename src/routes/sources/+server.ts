import type { RequestHandler } from "./$types";

import { json } from "@sveltejs/kit";
import { readFileSync } from "node:fs";

export const GET: RequestHandler = async () => {
  const sources = Object.fromEntries(
    Object.keys(import.meta.glob("/src/python/**/*")).map((path) => {
      const content = readFileSync(`./${path}`, "utf-8");
      return [path.replace("/src/python/", ""), content];
    },
    ),
  );
  return json(sources);
};

export const prerender = true;

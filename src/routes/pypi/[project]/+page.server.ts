import type { PageServerLoad } from "./$types";

import { html2markdown } from "$lib/utils/html";
import { load as loadCheerio } from "cheerio";
import { parseDocument } from "htmlparser2";

export const load = (async ({ fetch, params: { project } }) => {
  const res = await fetch(`https://pypi.org/project/${project}/`).then(r => r.text());

  const $ = loadCheerio(parseDocument(res));

  const [name, version] = $(".package-header h1").text().trim().split(" ");

  let description: string | undefined = $(".package-description").text().trim();
  if (description === "No project description provided")
    description = undefined;

  const updated = $(".banner time").text().trim();

  const tags = $("#data .tags .package-keyword").map((_, el) => $(el).text().trim().replace(/,$/, "")).toArray();

  const readme = html2markdown($(".project-description").html()!);

  return { name, version, description, updated, tags, readme };
}) satisfies PageServerLoad;

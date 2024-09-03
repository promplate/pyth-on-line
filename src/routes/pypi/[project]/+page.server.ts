import type { PageServerLoad } from "./$types";
import type { RegistryResponse } from "./types";

import { html2markdown } from "$lib/utils/html";
import { load as loadCheerio } from "cheerio";
import { parseDocument } from "htmlparser2";

export const load = (async ({ fetch, params: { project } }) => {
  const [res, { info }] = await Promise.all([
    fetch(`https://pypi.org/project/${project}/`).then(r => r.text()),
    fetch(`https://pypi.org/pypi/${project}/json`).then(r => r.json()) as Promise<RegistryResponse>,
  ]);

  const $ = loadCheerio(parseDocument(res));

  const { name, version, summary: description } = info;

  const updated = $(".banner time").text().trim();

  const tags = $("#data .tags .package-keyword").map((_, el) => $(el).text().trim().replace(/,$/, "")).toArray();

  const readme = info.description_content_type === "text/markdown" ? info.description : html2markdown($(".project-description").html()!);

  return { name, version, description, updated, tags, readme };
}) satisfies PageServerLoad;

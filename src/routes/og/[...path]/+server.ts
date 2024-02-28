import type { RequestHandler } from "@sveltejs/kit";
import type { SvelteComponent } from "svelte";

import component from "./OG.svelte";
import { ImageResponse } from "@ethercorps/sveltekit-og";
import { cast } from "$lib/utils/typing";

export const GET: RequestHandler = async ({ url: { origin }, params }) => {
  const path: string = params.path ?? "";

  const context: { href: string; title?: string; subtitle?: string } = { href: `${origin}/${decodeURI(path)}` };

  if (path === "") {
    context.title = "Python Console";
    context.subtitle = "Just a Python Console";
  }

  const html = cast<SvelteComponent>(component).render(context).html.replaceAll("class=", "tw=");
  return new ImageResponse(html);
};

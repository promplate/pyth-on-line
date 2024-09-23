import type { RequestHandler } from "@sveltejs/kit";
import type { SvelteComponent } from "svelte";

import component from "./OG.svelte";
import { ImageResponse } from "@ethercorps/sveltekit-og";
import { cast } from "$lib/utils/typing";

export const GET: RequestHandler = async ({ url: { origin }, params }) => {
  const path: string = params.path ?? "";

  const context: any = { origin, path };

  if (path === "") {
    context.title = "AI-supercharged online python IDE";
    context.subtitle = "Powered by Pyodide, a WASM build of CPython";
  }

  const html = cast<SvelteComponent>(component).render(context).html.replaceAll("class=", "tw=");
  return new ImageResponse(html);
};

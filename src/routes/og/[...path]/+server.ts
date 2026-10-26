import type { RequestHandler } from "@sveltejs/kit";

import component from "./OG.svelte";
import { ImageResponse } from "@ethercorps/sveltekit-og";
import { render } from "svelte/server";

export const GET: RequestHandler = async ({ url: { origin }, params }) => {
  const path: string = params.path ?? "";

  const context: any = { origin, path };

  if (path === "") {
    context.title = "AI-supercharged online python IDE";
    context.subtitle = "Powered by Pyodide, a WASM build of CPython";
  }

  const html = render(component, { props: context }).body.replaceAll("class=", "tw=");
  return new ImageResponse(html);
};

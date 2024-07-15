import { redirect } from "@sveltejs/kit";

export async function load() {
  redirect(307, "/console");
}

export const prerender = true;

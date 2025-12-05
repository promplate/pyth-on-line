import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ fetch, url }) => {
  const response = await fetch(url.pathname, { headers: { accept: "application/json" } });
  if (!response.ok) {
    const message = await response.text().catch(() => response.statusText);
    throw new Error(message || "Failed to fetch file data");
  }
  return { payload: await response.json() };
};

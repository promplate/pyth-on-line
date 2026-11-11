import type { Handle } from "@sveltejs/kit/hooks";

const homepageFonts = new Set([
  "node_modules/@fontsource-variable/inter/files/inter-latin-wght-normal.woff2",
  "node_modules/@fontsource-variable/fira-code/files/fira-code-latin-wght-normal.woff2",
]);

export const handle: Handle = ({ event, resolve }) => resolve(event, {
  preload: asset => asset.type === "js" || asset.type === "css" || (asset.type === "font" && event.route.id === "/" && homepageFonts.has(asset.filename)),
});

import type { Handle } from "@sveltejs/kit/hooks";

const homepageFonts = /(?:^|[/\\])(?:inter|fira-code)-latin-wght-normal\.woff2$/;

export const handle: Handle = ({ event, resolve }) => resolve(event, {
  preload: asset => asset.type === "js" || asset.type === "css" || (asset.type === "font" && event.route.id === "/" && homepageFonts.test(asset.filename)),
});

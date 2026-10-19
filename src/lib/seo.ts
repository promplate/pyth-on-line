import { defaultMetadata, Metadata } from "./metadata.svelte";
import { afterNavigate } from "$app/navigation";
import { createContext, untrack } from "svelte";

type SEOMetadata = typeof defaultMetadata;
const [getMetadata, setMetadata] = createContext<Metadata>();

export function initMetadata() {
  return setMetadata(new Metadata());
}

export function resetMetadata(metadata: Metadata) {
  Object.assign(metadata, defaultMetadata);
}

export function updateMetadata(metadata: Partial<SEOMetadata> | (() => Partial<SEOMetadata>)) {
  const current = getMetadata();
  // Route callbacks are evaluated at setup/navigation, independently of the rendering reaction.
  const update = () => untrack(() => Object.assign(current, typeof metadata === "function" ? metadata() : metadata));
  update();
  afterNavigate(update);
}

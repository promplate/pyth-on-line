import { defaultMetadata, Metadata } from "./metadata.svelte";
import { afterNavigate } from "$app/navigation";
import { createContext, untrack } from "svelte";

const [getMetadata, setMetadata] = createContext<Metadata>();

export function initMetadata() {
  return setMetadata(new Metadata());
}

export function resetMetadata(metadata: Metadata) {
  metadata.source = defaultMetadata;
}

export function updateMetadata(metadata: Metadata["source"]) {
  const current = getMetadata();
  // Keep the getter reactive; evaluating it here would freeze route props until navigation.
  const update = () => untrack(() => current.source = metadata);
  update();
  afterNavigate(update);
}

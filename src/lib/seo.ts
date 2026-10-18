import type { Writable } from "svelte/store";

import { afterNavigate } from "$app/navigation";
import { createContext } from "svelte";
import { writable } from "svelte/store";

const defaultMetadata = {
  ogTitle: "Python Online",
  ogDescription: "A simple online python console",
};

type SEOMetadata = typeof defaultMetadata;
const [getMetadata, setMetadata] = createContext<Writable<SEOMetadata>>();

export function initMetadataStore() {
  return setMetadata(writable(defaultMetadata));
}

export function resetMetadata(store: Writable<SEOMetadata>) {
  store.set(defaultMetadata);
}

export function updateMetadata(metadata: Partial<SEOMetadata> | (() => Partial<SEOMetadata>)) {
  const store = getMetadata();
  const update = () => store.update(current => ({ ...current, ...(typeof metadata === "function" ? metadata() : metadata) }));
  update();
  afterNavigate(update);
}

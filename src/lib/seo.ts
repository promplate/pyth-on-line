import type { Writable } from "svelte/store";

import { getContext, setContext } from "svelte";
import { writable } from "svelte/store";

const defaultMetadata = {
  ogTitle: "Python Online",
  ogDescription: "A simple online python console",
};

type SEOMetadata = typeof defaultMetadata;

export function initMetadataStore() {
  return setContext("seo-metadata", writable(defaultMetadata));
}

export function updateMetadata(metadata: Partial<SEOMetadata>) {
  const store = getContext<Writable<SEOMetadata>>("seo-metadata");
  store.update(current => ({ ...current, ...metadata }));
}

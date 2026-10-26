export const defaultMetadata = {
  ogTitle: "Python Online",
  ogDescription: "A simple online python console",
};

export class Metadata {
  source = $state.raw<Partial<typeof defaultMetadata> | (() => Partial<typeof defaultMetadata>)>(defaultMetadata);
  #values = $derived(typeof this.source === "function" ? this.source() : this.source);
  ogTitle = $derived(this.#values.ogTitle ?? defaultMetadata.ogTitle);
  ogDescription = $derived(this.#values.ogDescription ?? defaultMetadata.ogDescription);
}

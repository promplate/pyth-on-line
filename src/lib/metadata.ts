import { writable } from "svelte/store";

/**
 * SEO Metadata interface defining all possible metadata fields
 */
export interface SEOMetadata {
  title?: string;
  description?: string;
  image?: string;
  type?: string;
  url?: string;
  siteName?: string;
  twitterCard?: string;
  themeColor?: string;
}

/**
 * Metadata store interface - maps URLs to their SEO metadata
 */
export interface MetadataStore {
  [url: string]: SEOMetadata;
}

/**
 * Global metadata store that maps URLs to their SEO parameters
 * This allows different pages to have different metadata while maintaining
 * a single source of truth for SEO data.
 */
export const metadataStore = writable<MetadataStore>({});

/**
 * Default metadata values used as fallbacks when specific metadata isn't provided
 */
export const defaultMetadata: SEOMetadata = {
  title: "Python Online",
  description: "A simple online python console",
  type: "website",
  twitterCard: "summary_large_image",
  themeColor: "#171717",
};

/**
 * Updates metadata for a specific URL path
 * @param url - The URL/path to update metadata for (e.g., "/", "/about", "/playground")
 * @param metadata - Partial SEO metadata to update (only provided fields will be updated)
 *
 * @example
 * ```ts
 * updateMetadata("/about", {
 *   title: "About - Python Online",
 *   description: "Learn about our Python environment",
 *   type: "article"
 * });
 * ```
 */
export function updateMetadata(url: string, metadata: Partial<SEOMetadata>) {
  metadataStore.update(store => ({
    ...store,
    [url]: {
      ...store[url],
      ...metadata,
    },
  }));
}

/**
 * Retrieves metadata for a specific URL with fallback to defaults
 * @param url - The URL to get metadata for
 * @param store - The current metadata store state
 * @returns Combined metadata with defaults applied for missing fields
 */
export function getMetadata(url: string, store: MetadataStore): SEOMetadata {
  return {
    ...defaultMetadata,
    ...store[url],
  };
}

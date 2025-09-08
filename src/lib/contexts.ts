import type { SEOMetadata } from "./metadata";

/**
 * Context key for the metadata context
 */
export const METADATA_CONTEXT_KEY = "metadata";

/**
 * Metadata context interface provided to child components
 * This allows any component in the app to update SEO metadata for any URL
 */
export interface MetadataContext {
  /**
   * Update metadata for a specific URL
   * @param url - The URL/path to update metadata for
   * @param metadata - Partial SEO metadata to update
   */
  updateMetadata: (url: string, metadata: Partial<SEOMetadata>) => void;
}

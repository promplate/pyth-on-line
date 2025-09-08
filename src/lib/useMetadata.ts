import type { MetadataContext } from "./contexts";
import type { SEOMetadata } from "./metadata";

import { METADATA_CONTEXT_KEY } from "./contexts";
import { getContext } from "svelte";

/**
 * React-style hook to get the metadata context and update metadata for pages
 * Must be called from within a component that has access to the MetadataContext
 *
 * @returns MetadataContext with updateMetadata function
 * @throws Error if used outside of MetadataContext
 *
 * @example
 * ```svelte
 * <script lang="ts">
 *   import { onMount } from "svelte";
 *   import { page } from "$app/stores";
 *   import { useMetadata } from "$lib/useMetadata";
 *
 *   const { updateMetadata } = useMetadata();
 *
 *   onMount(() => {
 *     updateMetadata($page.url.pathname, {
 *       title: "My Page - Python Online",
 *       description: "This is my custom page description",
 *       type: "article"
 *     });
 *   });
 * </script>
 * ```
 */
export function useMetadata() {
  const context = getContext<MetadataContext>(METADATA_CONTEXT_KEY);

  if (!context) {
    throw new Error("useMetadata must be used within a component that has MetadataContext");
  }

  return context;
}

/**
 * Utility function to update metadata for the current page
 * This is a convenience wrapper around useMetadata()
 *
 * @param url - The URL/path for which to update metadata
 * @param metadata - Partial SEO metadata to update
 *
 * @example
 * ```ts
 * setPageMetadata("/my-page", {
 *   title: "My Page",
 *   description: "This is my page"
 * });
 * ```
 */
export function setPageMetadata(url: string, metadata: Partial<SEOMetadata>) {
  const { updateMetadata } = useMetadata();
  updateMetadata(url, metadata);
}

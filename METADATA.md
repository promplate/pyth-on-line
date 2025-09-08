# SEO Metadata Context API

This implementation provides a URL-based metadata system that allows pages to dynamically update SEO parameters through Svelte's Context API.

## Features

- **URL-based metadata mapping**: Each URL can have its own SEO metadata
- **Context API integration**: Any component can update metadata for any URL
- **Reactive updates**: Metadata changes are automatically reflected in the page head
- **Fallback defaults**: Sensible defaults are provided for all metadata fields
- **TypeScript support**: Full type safety for all metadata operations

## Usage

### In a page component:

```svelte
<script lang="ts">
  import { page } from "$app/stores";
  import { useMetadata } from "$lib/useMetadata";
  import { onMount } from "svelte";

  const { updateMetadata } = useMetadata();

  onMount(() => {
    updateMetadata($page.url.pathname, {
      title: "My Page - Python Online",
      description: "This is my custom page description",
      type: "article",
      image: "/my-custom-image.png",
    });
  });
</script>

<h1>My Page Content</h1>
```

### Available metadata fields:

```typescript
interface SEOMetadata {
  title?: string; // Page title
  description?: string; // Meta description
  image?: string; // OG/Twitter image URL
  type?: string; // OG type (website, article, etc.)
  url?: string; // Canonical URL
  siteName?: string; // OG site name
  twitterCard?: string; // Twitter card type
  themeColor?: string; // Browser theme color
}
```

### Direct function usage:

```typescript
import { updateMetadata } from "$lib/metadata";

// Update metadata directly
updateMetadata("/my-page", {
  title: "My Page",
  description: "This is my page"
});
```

## Implementation Details

The system consists of:

1. **`metadataStore`**: A Svelte writable store mapping URLs to metadata
2. **`MetadataContext`**: Context API providing `updateMetadata` function
3. **Root Layout**: Reactively updates `<meta>` tags based on current URL
4. **`useMetadata` hook**: Easy access to metadata context in components

All metadata is stored in memory and persists during the session. The layout automatically picks up the metadata for the current URL and applies fallbacks from `defaultMetadata` for any missing fields.

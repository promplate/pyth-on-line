<script lang="ts">
  import readme from "../../../../README.md?raw";
  import { page } from "$app/stores";
  import Notebook from "$lib/components/notebook/Notebook.svelte";
  import { useMetadata } from "$lib/useMetadata";
  import { onMount } from "svelte";

  const { updateMetadata } = useMetadata();

  onMount(() => {
    // Update metadata for this page
    updateMetadata($page.url.pathname, {
      title: "About - Python Online",
      description: "Learn about Python Online - an interactive Python environment running in your browser with Pyodide",
      type: "article",
    });
  });
</script>

<Notebook text={readme} />

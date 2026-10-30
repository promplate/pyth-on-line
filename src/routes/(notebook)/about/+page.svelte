<script lang="ts">
  import readme from "./intro.md?raw";
  import Notebook from "#lib/components/notebook/Notebook.svelte";
  import { updateMetadata } from "#lib/seo.js";

  updateMetadata({ ogTitle: "Python Online Tour", ogDescription: "Explore Python Online with an interactive notebook." });
</script>

<Notebook text={readme} />

<script lang="ts">
  import files from "../../../python";
  import Workspace from "../Workspace.svelte";
  import { updateMetadata } from "#lib/seo.js";

  updateMetadata({ ogTitle: "Python Playground", ogDescription: "Edit and run Python files in an isolated browser workspace." });
</script>

<Workspace sources={files} />

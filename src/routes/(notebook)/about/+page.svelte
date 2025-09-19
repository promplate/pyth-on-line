<script lang="ts">
  import readme from "./intro.md?raw";
  import Notebook from "$lib/components/notebook/Notebook.svelte";
</script>

<Notebook text={readme} />

<script lang="ts">
  import type { PageData } from "./$types";

  import Workspace from "../../Workspace.svelte";

  export let data: PageData;

  const { sources } = data;
</script>

<Workspace {sources} />
